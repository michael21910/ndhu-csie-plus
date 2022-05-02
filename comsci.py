from charset_normalizer import detect
from tensorflow.keras import models
from gensim.models import Word2Vec
import nltk
import numpy as np
import requests
from langid.langid import LanguageIdentifier, model
import json

nltk.download('all')

identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)

word_set = set(nltk.corpus.words.words())
stop_set = set(nltk.corpus.stopwords.words())
lemm = nltk.stem.WordNetLemmatizer()

words_model_name = "./models/words_model.model"
class_model_name = "./models/class_model.h5"

words_model = Word2Vec.load(words_model_name)
class_model = models.load_model(class_model_name)

words_limit = 100
vector_size = words_model.vector_size

def convert(tag):
    char = tag[0].lower()
    if char == 'j':
        return nltk.corpus.wordnet.ADJ
    elif char == 'r':
        return nltk.corpus.wordnet.ADV
    elif char == 'v':
        return nltk.corpus.wordnet.VERB
    else:
        return nltk.corpus.wordnet.NOUN

def pre_process(string):
    # translate the string if the language is not English
    detect = identifier.classify(string)
    print(detect)
    if detect[0] != "en" or detect[1] < 0.95:
        #string = string.replace('\n', ' ').replace('\t', ' ').replace('　', ' ')
        url = "http://translate.google.cn/translate_a/single?client=gtx&dt=t&dj=1&ie=UTF-8&sl={}&tl=en&q={}".format(detect[0], string)
        string = ""
        #a = requests.get(url).text
        #print(a, type(a))
        target = json.loads(requests.get(url).text)
        for i in range(len(target['sentences'])):
            string += target['sentences'][i]['trans'] + " "
        print(string)
    else:
        print('Original sentence.')
        print(string)

    string = nltk.tokenize.word_tokenize(string)
    string = nltk.pos_tag(string)
    result = []
    
    lower_string = [  (x[0].lower(), x[1]) for x in string  ]
    for i in range(len(string)):
        if not(string[i][0] in stop_set or lower_string[i][0] in stop_set):
            cute_word = lemm.lemmatize(string[i][0], pos = convert(string[i][1]))
            bird_word = lemm.lemmatize(lower_string[i][0], pos = convert(lower_string[i][1]))
            if cute_word in word_set:
                result.append(cute_word)
            elif bird_word in word_set:
                result.append( bird_word )
            else:
                print("Not stopword: ", string[i], lower_string[i])
        else:
            print("Is stopword: ", string[i], lower_string[i])
    del string
    del lower_string
    return result

def preprocess_vectorize_without_translate(string):

    string = nltk.tokenize.word_tokenize(string)
    string = nltk.pos_tag(string)
    result = []
    
    lower_string = [  (x[0].lower(), x[1]) for x in string  ]
    for i in range(len(string)):
        if not(string[i][0] in stop_set or lower_string[i][0] in stop_set):
            cute_word = lemm.lemmatize(string[i][0], pos = convert(string[i][1]))
            bird_word = lemm.lemmatize(lower_string[i][0], pos = convert(lower_string[i][1]))
            if cute_word in word_set:
                result.append(cute_word)
            elif bird_word in word_set:
                result.append( bird_word )
            else:
                print("Not stopword: ", string[i], lower_string[i])
        else:
            print("Is stopword: ", string[i], lower_string[i])
    del string
    del lower_string
    return vectorize_str(result)

def vectorize_str(string_list):
    """
    string_list = [  string for string in string_list if (string in words_model.wv)  ] 
    list_length = len(string_list)
    string_list = string_list * (words_limit // list_length) + [string_list[i] for i in range(0, words_limit % (list_length))]
    return np.expand_dims(np.stack([  words_model.wv[string] for string in string_list  ]), axis = 0)
    """
    string_list = [  word for word in string_list if (word in word_set)  ]
    string_list = string_list + [ None ] * max(0, (words_limit - len(string_list)))
    vectorized_data = np.stack([
        words_model.wv[word] if (word != None) else (np.zeros((words_model.vector_size, ))) for word in string_list[ : words_limit ]  
    ])    
    #return np.expand_dims(vectorized_data, axis = 0)
    return np.expand_dims(vectorized_data.T, axis = 0)

def get_relation_score(vectorized_data):
    return class_model.predict(vectorized_data)[0][0]