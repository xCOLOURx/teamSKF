import json
import logging
from flask import request, jsonify

from routes import app

logger = logging.getLogger(__name__)


def compute_time_for_scenario(intel, reserve, fronts, stamina_full):
    """
    Simulate the sequence of attacks and cooldowns and return total time in minutes.
    Rules implemented:
      - Start with mana = reserve, stamina = stamina_full.
      - For each intel entry (front, mp_cost) in order:
          * If mp_cost <= mana AND stamina > 0 -> perform attack:
              - If the previous action was an attack AND previous_front == front (and no cooldown since),
                this attack is an extension and costs 0 minutes (but still uses mp and consumes 1 stamina).
              - Otherwise it costs 10 minutes.
              - Deduct mp_cost from mana and reduce stamina by 1.
          * Else -> cooldown (10 minutes), restore mana to reserve and stamina to stamina_full.
              After cooldown, retry the same intel entry.
      - After all intel entries are handled, perform a final cooldown (10 minutes) so Klein can immediately
        join the expedition.
    """
    mana = reserve
    stamina = stamina_full
    total_time = 0

    prev_front = None
    prev_action_was_attack = False  # becomes False if a cooldown happens

    i = 0
    n = len(intel)
    while i < n:
        front, cost = intel[i]

        # Validate ranges (briefly). If invalid, treat as cannot perform -> cooldown loop will handle it.
        if not (1 <= front <= fronts) or not (1 <= cost <= reserve):
            # invalid intel entry -- log and treat as needing a cooldown then skip (defensive)
            logger.warning("Invalid intel entry: front=%r, cost=%r. Skipping.", front, cost)
            # To avoid infinite loop, just advance and continue
            i += 1
            prev_action_was_attack = False
            prev_front = None
            # still require cooldown after loop; no extra time added here
            continue

        # If we have enough mana and stamina to cast
        if cost <= mana and stamina > 0:
            # determine time for this attack
            if prev_action_was_attack and prev_front == front:
                # extension: 0 minutes
                add_time = 0
            else:
                add_time = 10

            total_time += add_time
            mana -= cost
            stamina -= 1

            prev_front = front
            prev_action_was_attack = True

            # move to next intel entry
            i += 1
        else:
            # need to cooldown before we can proceed
            total_time += 10
            mana = reserve
            stamina = stamina_full
            prev_action_was_attack = False
            prev_front = None
            # after cooldown we will retry same intel entry

    # final cooldown required so he can immediately join the expedition
    total_time += 10

    return total_time



@app.route('/the-mages-gambit', methods=['POST'])
def mage():
    payload = request.get_json(force=True)

    # Log the raw input for debugging
    logger.info("Received request payload: %s", payload)

    results = []
    for idx, scenario in enumerate(payload):
        intel = scenario.get("intel", [])
        reserve = int(scenario.get("reserve"))
        fronts = int(scenario.get("fronts"))
        stamina = int(scenario.get("stamina"))

        # normalize intel entries to tuples of ints
        parsed_intel = []
        for pair in intel:
            if not (isinstance(pair, (list, tuple)) and len(pair) == 2):
                raise ValueError("intel entries must be pairs [front, mp]")
            f, c = int(pair[0]), int(pair[1])
            parsed_intel.append((f, c))

        logger.debug(
            "Scenario %d -> intel=%s, reserve=%d, fronts=%d, stamina=%d",
            idx, parsed_intel, reserve, fronts, stamina
        )

        time_needed = compute_time_for_scenario(parsed_intel, reserve, fronts, stamina)
        results.append({"time": time_needed})

    logger.info("Computed results: %s", results)
    return jsonify(results), 200
