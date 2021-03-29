from flask import Flask, request, jsonify
# export FLASK_APP=server.py

from gadvi.recommenders import LightFMBased

# initialize flask application
app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
model_path = 'scripts/resources/models//model_light_fm_simple_256_warp.pickle'
dataset_path = 'scripts/resources/models/model_light_fm_simple_256_warp_dataset.pickle'
data_path = 'scripts/resources/models//model_light_fm_simple_256_warp_data.pickle'

model = LightFMBased()
model.load(model_path, dataset_path, data_path)


# Predict route takes one argument: player id
@app.route('/predict')
def predict():
    player = request.args.get('playerid')
    if player is None:
        return jsonify(data=None, message="Required parameter is missing", statusCode=400, isError=True)
    else:
        predictions = model.predict(player)  # "Player_13893025"

        return jsonify(data=predictions, message="Success", statusCode=200, isError=False)


@app.route('/')
def info():
    info = model.get_info()
    return jsonify(data=info, message="Success", statusCode=200, isError=False)


@app.errorhandler(500)
def internal_server_error(e):
    return jsonify(message=str(e), statusCode=500, isError=True)


@app.errorhandler(404)
def not_found_error(e):
    return jsonify(message=str(e), statusCode=404, isError=True)


if __name__ == '__main__':
     app.run(debug=True, port=5000)
