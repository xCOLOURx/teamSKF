from flask import Flask
from flask import json
app = Flask(__name__)
json.provider.DefaultJSONProvider.ensure_ascii = False
import routes.square
import routes.blankety
import routes.princess_diaries
import routes.ubs
import routes.trading_formula
import routes.trading_bot
import routes.ink_archive
import routes.trivia
import routes.mst_calculation
import routes.sailing_club
import routes.slpu
import routes.ticketing_agent
import routes.duolingo_sort
import routes.operation_safeguard
import routes.the_mage_gambit
import routes.ctf