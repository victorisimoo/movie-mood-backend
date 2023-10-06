# -*- coding: utf-8 -*-
import json

from flask import Flask, request, jsonify
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader, LLMPredictor, ServiceContext, StorageContext, \
    load_index_from_storage
from langchain import OpenAI
from flask_cors import CORS
import os

app = Flask(__name__)
uri = "mongodb+srv://movie-mood:bzqk8Yademoviemood@cluster0.acn6syr.mongodb.net/?retryWrites=true&w=majority"
os.environ["OPENAI_API_KEY"] = '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'
client = MongoClient(uri, server_api=ServerApi('1'))


# ------------------------- DATABASE -------------------------

CORS(app, resources={r"/api/*": {"origins": "http://localhost:4200"}})
# endpoint to check if the database is connected
@app.route('/api/database-ping', methods=['GET'])
def get_database_connect():
    try:
        client.admin.command('ping')
        return jsonify({'message': 'Connection successful'}), 200
    except Exception as e:
        return jsonify({'error': 'Connection failed', 'message': str(e)}), 500


# ------------------------- USERS -------------------------

#pagina de login digamos
# endpoint to create new user
@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or not all(key in data for key in ['first_name', 'last_name', 'username', 'email']):
        return jsonify({'error': 'Bad Request', 'message': 'Missing required fields'}), 400
    user_id = client.db.users.insert_one(data).inserted_id
    return jsonify({'message': 'User created successfully', 'user_id': str(user_id)}), 201


# endpoint to get all users
@app.route('/api/users', methods=['GET'])
def get_all_users():
    users = client.db.users.find()
    return jsonify([{'_id': str(user['_id']), 'first_name': user['first_name'], 'last_name': user['last_name'],
                     'username': user['username'], 'email': user['email']} for user in users]), 200


# endpoint to get user by id
@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    user = client.db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'error': 'Not Found', 'message': 'User not found'}), 404
    return jsonify({'_id': str(user['_id']), 'first_name': user['first_name'], 'last_name': user['last_name'],
                    'username': user['username'], 'email': user['email'], 'categories': user['movies_categories']}), 200


# endpoint to update user by id
@app.route('/api/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    if not data or not all(key in data for key in ['first_name', 'last_name', 'username', 'email']):
        return jsonify({'error': 'Bad Request', 'message': 'Missing required fields'}), 400
    user = client.db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'error': 'Not Found', 'message': 'User not found'}), 404
    client.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': data})
    return jsonify({'message': 'User updated successfully'}), 200


# endpoint to delete user by id
@app.route('/api/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = client.db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'error': 'Not Found', 'message': 'User not found'}), 404
    client.db.users.delete_one({'_id': ObjectId(user_id)})
    return jsonify({'message': 'User deleted successfully'}), 200


# endpoint to get user by username
@app.route('/api/users/username/<username>', methods=['GET'])
def get_user_by_username(username):
    user = client.db.users.find_one({'username': username})
    if not user:
        return jsonify({'error': 'Not Found', 'message': 'User not found'}), 404
    return jsonify({'_id': str(user['_id']), 'first_name': user['first_name'], 'last_name': user['last_name'],
                    'username': user['username'], 'email': user['email']}), 200


# endpoint to get user by email
@app.route('/api/users/email/<email>', methods=['GET'])
def get_user_by_email(email):
    user = client.db.users.find_one({'email': email})
    if not user:
        return jsonify({'error': 'Not Found', 'message': 'User not found'}), 404
    return jsonify({'_id': str(user['_id']), 'first_name': user['first_name'], 'last_name': user['last_name'],
                    'username': user['username'], 'email': user['email']}), 200


# ------------------------- MOVIES CATEGORIES -------------------------

# endpoint to add movie category to user
##categorias al usuario
@app.route('/api/users/<user_id>/movies-categories', methods=['POST'])
def add_movie_category(user_id):
    data = request.get_json()
    if not data or not all(key in data for key in ['categories']):
        return jsonify({'error': 'Bad Request', 'message': 'Missing required fields'}), 400
    user = client.db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'error': 'Not Found', 'message': 'User not found'}), 404
    client.db.users.update_one({'_id': ObjectId(user_id)}, {'$push': {'movies_categories': data}})
    return jsonify({'message': 'Categories added successfully'}), 201


# ------------------------- ANALYSIS -------------------------
##endpoint
# endpoint to get data for user analysis
@app.route('/api/users/<user_id>/analysis', methods=['POST'])
def get_user_analysis(user_id):
    print(request.get_json())
    data = request.get_json()
    
    if not data or not all(key in data for key in ['age', 'sex', 'state_of_mind', 'film_one', 'film_two',
                                                   'film_three']):
        return jsonify({'error': 'Bad Request', 'message': 'Missing required fields'}), 400
    user = client.db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'error': 'Not Found', 'message': 'User not found'}), 404

    # adding analysis data to user
    user_data = {
        'age': data['age'],
        'sex': data['sex'],
        'state_of_mind': data['state_of_mind'],
        'film_one': data['film_one'],
        'film_two': data['film_two'],
        'film_three': data['film_three'],
        'categories': user['movies_categories'][0]['categories']
    }

    # prompt for chatbot
    #prompt = f""" I want you to act as a movie recommender. I need you to take into account the following user requirements for each of the recommendations: their gender is {''.join(user_data['sex'])}, their age is {''.join(user_data['age'])}, their mood is {''.join(user_data['state_of_mind'])}, their favourite movie genres are {', '.join(user_data['categories'])} and their favourite reference movies are {''.join(user_data['film_one'])} {''.join(user_data['film_two'])} y {''.join(user_data['film_three'])} Recommend movies from the data you were trained with, recommend  movies that are classified according to the user's age. When recommending a movie, please return the title, the year, the genres, the href, the extract and the thumbnail, this information is in the data you were trained with, this, in a json format, and recommend maximum 3 movies. """
    prompt = f""" I want you to act as a movie recommender. I need you to take into account the following user requirements for each of the recommendations: their gender is {user_data['sex']}, their age is {user_data['age']}, their mood is {user_data['state_of_mind']}, their favourite movie genres are {', '.join(user_data['categories'])} and their favourite reference movies are {user_data['film_one']} {user_data['film_two']} y {user_data['film_three']} Recommend movies from the data you were trained with, recommend movies that are classified according to the user's age. When recommending a movie, please return the title, the year, the genres, the href, the extract and the thumbnail, this information is in the data you were trained with, this, in a json format, and recommend 3 movies exactly. """

    response_gpt = chatbot(prompt)
    response_gpt = json.loads(response_gpt)
    response_gpt = json.dumps(response_gpt, indent=None, separators=(',', ':'))
    client.db.users.update_one({'_id': ObjectId(user_id)}, {'$push': {'recommended_films': json.loads(response_gpt)['movies']}})
    return jsonify({'message': 'Analysis data retrieved successfully', 'response': json.loads(response_gpt)}), 200


@app.route('/api/train-model', methods=['GET'])
def train_model():
    index = construct_index("data-training")
    return jsonify({'message': 'Model trained successfully'}), 200

##chatbot
@app.route('/api/chatbot', methods=['POST'])
def chatbot_response():
    data = request.get_json()
    if not data or not all(key in data for key in ['input_text']):
        return jsonify({'error': 'Bad Request', 'message': 'Missing required fields'}), 400
    response = chatbot(data['input_text'])
    return jsonify({'message': 'Chatbot response retrieved successfully', 'response': response}), 200


# method to construct index
def construct_index(directory_path):
    # set number of output tokens
    num_outputs = 1000
    _llm_predictor = LLMPredictor(llm=OpenAI(temperature=0.4, model_name="gpt-4", max_tokens=num_outputs))
    service_context = ServiceContext.from_defaults(llm_predictor=_llm_predictor)
    docs = SimpleDirectoryReader(directory_path).load_data()
    index = GPTVectorStoreIndex.from_documents(docs, service_context=service_context)

    # Directory in which the indexes will be stored
    index.storage_context.persist(persist_dir="indexes")
    return index


# chatbot function
def chatbot(input_text):
    # rebuild storage context
    storage_context = StorageContext.from_defaults(persist_dir="indexes")
    # load indexes from directory using storage_context
    query_engne = load_index_from_storage(storage_context).as_query_engine()
    response = query_engne.query(input_text)
    # returning the response
    return response.response


if __name__ == '__main__':
    app.run(debug=True)
