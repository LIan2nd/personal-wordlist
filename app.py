# Import Package
import os
from datetime import datetime
from os.path import join, dirname
from dotenv import load_dotenv

from flask import (
    Flask,
    request,
    render_template,
    redirect,
    url_for,
    jsonify
)
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import requests

# Setup

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")
API_KEY = os.environ.get("API_KEY")
BASE_URL = "https://www.dictionaryapi.com/api/v3/references/"

client = MongoClient(MONGODB_URI)

db = client[DB_NAME]
app = Flask(__name__)

@app.route('/')
def main():
    words_result = db.words.find({}, {'_id': False})
    words = []
    for word in words_result:
        i = 0
        if not word['definitions'][i] : 
          i = i + 1
        definition = word['definitions'][i]['shortdef']
           
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definition': definition,
        })

    return render_template(
        'index.html',
        words=words,
    )

@app.route('/error')
def error() :
  words_result = db.words.find({}, {'_id': False})
  words = []
  for word in words_result:
        i = 0
        if not word['definitions'][i] : 
          i = i + 1
        definition = word['definitions'][i]['shortdef']
           
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definition': definition,
        })
    
  msg = request.args.get('msg')
  meanWord = request.args.get('meanWord')
  meanWord = meanWord.split(', ') if meanWord else []
  word = request.args.get('word')
  notFound = request.args.get('notFoundWord')
  return render_template('error.html', 
      words=words,
      word=word,
      msg=msg,
      mean=meanWord,
      notFound=notFound
  )

@app.route('/detail/<keyword>')
def detail(keyword) : 
  url = f'{BASE_URL}collegiate/json/{keyword}?key={API_KEY}'
  words = requests.get(url)
  definitions = words.json()

  if not definitions:
        return redirect(url_for(
            'error',
            notFoundWord=True,
            msg=f'Could not find ',
            word=keyword
        ))

  if type(definitions[0]) is str:
      return redirect(url_for(
          'error',
          word = keyword,
          msg=f'Could not find ', 
          meanWord = ", ".join(definitions),
      ))

  
  word = keyword
  return render_template('detail.html', word=word, definitions=definitions, status=request.args.get("status", "new"))

@app.route('/detail')
def blankDetail() :
  words_result = db.words.find({}, {'_id': False})
  words = []
  for word in words_result:
        i = 0
        if not word['definitions'][i] : 
          i = i + 1
        definition = word['definitions'][i]['shortdef']
          
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definition': definition,
        })
  suggest = ["Halo", "This", "cheese", "moon", "sun", "alpha", "beta", "sparta", "vocab", "car", "cat", "fish", "dolphin", "glass", "electronic", "phone", "laptop", "keyboard", "etc", "lets", "search", "the", "word"]
  msg = "Let's find the word first"
  return render_template('blankDetail.html', 
    msg=msg,
    words=words,
    suggests = suggest
  )

@app.route('/api/save_word', methods=["POST"])
def save_word() :

  json_data = request.get_json()
  word = json_data.get('word')
  definitions = json_data.get('definitions')
  doc = {
    "word" : word,
    "definitions" : definitions,
    "date" : datetime.now().strftime("%Y-%m-%d")
  }
  db.words.insert_one(doc)
  return jsonify({
    "result" : "success",
    "msg" : f"the word {word} was saved"
  })

@app.route('/api/delete_word', methods=['POST'])
def delete_word():
    word = request.form.get('word')
    db.words.delete_one({'word': word})
    db.examples.delete_many({'word': word})
    return jsonify({
        'result': 'success',
        'msg': f'the word {word} and all examples was deleted'
    })

@app.route('/api/get_exs', methods=['GET'])
def get_exs():
    word = request.args.get("word")
    example_data = db.examples.find({"word": word})
    examples = []
    for example in example_data :
       examples.append({
          "example" : example.get('example'),
          "id" : str(example.get('_id'))
       })
    return jsonify({
          'result': 'success',
          "examples": examples
        })

@app.route('/api/save_ex', methods=['POST'])
def save_ex():
    example = request.form.get('example')
    word = request.form.get('word')
    doc = {
       "word" : word,
       "example" : example
    }
    db.examples.insert_one(doc)
    return jsonify({
       'result': 'success',
       'ex' : example,
       'msg': f"your example, '{example}', was saved for {word} word"
       })


@app.route('/api/delete_ex', methods=['POST'])
def delete_ex():
  id = ObjectId(request.form.get('id'))
  example = db.examples.find_one({'_id': id})
  examplee = example['example']
  print(examplee)
  word = request.form.get('word')
  db.examples.delete_one({"_id": id})
  return jsonify({
     'result': 'success',
     'msg': f"your example, '{examplee}', was deleted from {word} word"
     })

port=5000
debug=True

if __name__ == "__main__":
  app.run('0.0.0.0', port=port, debug=debug)