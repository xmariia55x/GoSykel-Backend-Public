from flask import Flask
from blueprint.users import users
from blueprint.bycicle_lanes import bycicle_lanes
from blueprint.routes import routes
from blueprint.rankings import rankings
from mongoDB import disconnect_database

app = Flask(__name__)

app.secret_key = 'really strong secret key for gosykel project'
app.register_blueprint(users)
app.register_blueprint(bycicle_lanes)
app.register_blueprint(routes)
app.register_blueprint(rankings)

if __name__ == "__main__":
    app.run(port=5000)
    disconnect_database()
