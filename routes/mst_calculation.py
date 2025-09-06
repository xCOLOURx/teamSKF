import logging
import base64
import io


import cv2
import numpy as np
import pytesseract
import networkx as nx

from flask import request
from PIL import Image

from collections import defaultdict
from routes import app

import easyocr


pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


logger = logging.getLogger(__name__)


def decode_base64_image(base64_str):
    """Decode base64 string to OpenCV image (BGR)."""
    image_data = base64.b64decode(base64_str)
    image = Image.open(io.BytesIO(image_data))
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def extract_graph(image):
    """Extract graph nodes, edges, and weights from image using OpenCV + OCR."""

    # --- Step 1: Detect nodes (circles) ---
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    blurred = cv2.medianBlur(thresh, 5)

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=30,
        param1=50,
        param2=20,
        minRadius=10,
        maxRadius=50
    )

    nodes = []
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        for (x, y, r) in circles:
            nodes.append((x, y))

    
     # --- Step 2: Sample edge colors around each node ---
    def sample_edge_colors(image, nodes, radius=30, offset=20):
        """Sample edge colors around nodes and return node colors from the sampled points."""
        node_colors = defaultdict(list)  # This will hold node indices and their corresponding colors
        sampled_points = defaultdict(list)  # This will hold sampled points for each node
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        for i, (x, y) in enumerate(nodes):
            samples = []  # List to store sample colors for each node
            for angle in np.linspace(0, 2*np.pi, 720):  # every 0.5 degree
                dx = int((radius + offset) * np.cos(angle))
                dy = int((radius + offset) * np.sin(angle))
                px, py = x + dx, y + dy

                if 0 <= px < image.shape[1] and 0 <= py < image.shape[0]:
                    b, g, r = image[py, px]
                    h, s, v = hsv[py, px]

                    # Keep only colorful pixels (saturation and value thresholding)
                    if s > 80 and v > 50:
                        samples.append((int(b), int(g), int(r)))  # Store BGR color
                        sampled_points[i].append((px, py, (int(b), int(g), int(r))))  # Store point and color

            node_colors[i] = [color for color in samples]  # Directly assign the colors from the sampled points

        return dict(node_colors), sampled_points

    node_colors, sampled_points = sample_edge_colors(image, nodes)


    all_colors = []
    for colors in node_colors.values():
        for c in colors:
            if c not in all_colors:
                all_colors.append(c)

    def extract_weights_with_colors(image, edge_colors):
        """
        Extract weights based on edge colors using raw RGB/BGR color matching (no tolerance).
        """
        weights = []

        j = 0

        reader = easyocr.Reader(['en'], gpu=False)


        for color in edge_colors:
            # For each color in the edge_colors list
            # color is a tuple (B, G, R), e.g., (130, 41, 204)

            lower = np.array(color, dtype=np.uint8)  # Exact lower bound
            upper = np.array(color, dtype=np.uint8)  # Exact upper bound

            # Create a mask that identifies pixels with exactly this color
            mask = cv2.inRange(image, lower, upper)
            masked = cv2.bitwise_and(image, image, mask=mask)


            # Preprocess the masked image for OCR
            gray = cv2.cvtColor(masked, cv2.COLOR_BGR2GRAY)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            gray = cv2.bitwise_not(gray)


            def remove_line_direct(img, inpaint_radius=2):
                """
                Remove lines from a grayscale or color image using Hough Transform + inpainting.
                """
                # Ensure image is color (needed for inpainting to work well)
                if len(img.shape) == 2:  # grayscale → convert to BGR
                    color_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                else:
                    color_img = img.copy()

                # Detect edges
                edges = cv2.Canny(img, 50, 150)

                # Detect lines (sensitive to slanted ones too)
                lines = cv2.HoughLinesP(edges, 1, np.pi / 180,
                                        threshold= 60, minLineLength=100, maxLineGap=500)

                # Create proper binary mask
                mask = np.zeros(img.shape[:2], dtype=np.uint8)  # must be single-channel
                if lines is not None:
                    for line in lines:
                        x1, y1, x2, y2 = line[0]
                        cv2.line(mask, (x1, y1), (x2, y2), 255, thickness=4)

                # Inpaint the detected line regions
                inpainted = cv2.inpaint(color_img, mask, inpaint_radius, cv2.INPAINT_TELEA)

                # Return grayscale version for OCR
                return cv2.cvtColor(inpainted, cv2.COLOR_BGR2GRAY)

               

            # Example usage:
            result = remove_line_direct(gray)
            scale_factor = 5 # 2x, 3x, etc.
            result = cv2.resize(result, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

            _, thresh = cv2.threshold(result, 250, 255, cv2.THRESH_BINARY_INV)

            # Find coordinates of all non-zero (black text) pixels
            coords = cv2.findNonZero(thresh)  

            # Get bounding box of the text
            x, y, w, h = cv2.boundingRect(coords)

            # Add padding (e.g., 10 pixels around)
            padding = 10
            x_start = max(x - padding, 0)
            y_start = max(y - padding, 0)
            x_end = min(x + w + padding, result.shape[1])
            y_end = min(y + h + padding, result.shape[0])

            # Crop the image to the bounding box
            result = result[y_start:y_end, x_start:x_end]

            j += 1
            # cv2.imwrite("debug_gray" + str(j)+".png", result)


            # OCR with whitelist (digits only)
            # config = "--psm 6 -c tessedit_char_whitelist=0123456789"
            # data = pytesseract.image_to_data(result, output_type=pytesseract.Output.DICT, config=config)

            #print(data)

            # j += 1
            # cv2.imwrite("debug_gray" + str(j)+".png", result)

            data = reader.readtext(result, detail=1, paragraph=False)
            # print(data)

            digits = [text for (_, text, prob) in data if text.isdigit()][0]

            # print(digits)

           
            if digits.strip().isdigit():  # Ensure that the text is a digit
                weights.append({
                    "color": tuple(color),  # Original BGR color
                    "digit": int(digits),
                })


            # Extract digits and their positions
            # for i, text in enumerate(data["text"]):
            #     if text.strip().isdigit():  # Ensure that the text is a digit
            #         x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            #         print(text)
            #         weights.append({
            #             "color": tuple(color),  # Original BGR color
            #             "digit": int(text),
            #             "position": (x + w // 2, y + h // 2)
            #         })

        return weights




    weights = extract_weights_with_colors(image, all_colors)

    # --- Step 4: Build graph (color → weight association) ---
    G = nx.Graph()
    for i, node in enumerate(nodes):
        G.add_node(i, pos=node)

  

    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            common = set(node_colors[i]) & set(node_colors[j])
            if common:
                edge_color = list(common)[0]

                # Find matching weight for this edge color (direct comparison)
                weight_val = None
                for w in weights:
                    if tuple(w["color"]) == tuple(edge_color):  # exact color match
                        weight_val = w["digit"]
                        break

                if weight_val is not None:
                    G.add_edge(i, j, weight=weight_val)


    #print("Edges:", G.edges(data=True))

    return G




def compute_mst_weight(G):
    """Compute MST total weight using NetworkX."""
    if G.number_of_nodes() == 0:
        return 0
    mst = nx.minimum_spanning_tree(G, weight="weight")
    return int(sum(d["weight"] for _, _, d in mst.edges(data=True)))


@app.route('/mst-calculation', methods=['POST'])
def mst_calculation():
    data = request.get_json()
    logger.info("Data received for evaluation: %s", data)

    results = []
    for item in data:
        base64_img = item.get("image")
        img = decode_base64_image(base64_img)

        graph = extract_graph(img)
        mst_value = compute_mst_weight(graph)

        results.append({"value": mst_value})

    logger.info("Results: %s", results)
    return results




# if __name__ == "__main__":
#     with open("image.png", "rb") as f:
#         encoded = base64.b64encode(f.read()).decode("utf-8")
#         img = decode_base64_image(encoded)
#         graph = extract_graph(img)
#         print(graph)
#         mst_value = compute_mst_weight(graph)
#         print(mst_value)



