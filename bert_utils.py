from langid.langid import LanguageIdentifier, model
from tensorflow.keras import models
import requests, pickle, json, math, sys, re
sys.setrecursionlimit(100)
class SpaceInferrer:
    def __init__(self, frequency_vocabulary_file = "./words-by-frequency.txt"):
        self.wordlist = list(
            open(frequency_vocabulary_file, "r").read().split("\n")
        )
        self.wordlist = {  
            word : math.log((index + 1) * math.log(self.wordlist.__len__())) 
                for index, word in enumerate(self.wordlist)  
        }
    def union_with(self, new_set):
        set_size = self.wordlist.__len__()
        new_set  = list(filter(lambda x : x not in self.wordlist, new_set))
        new_size = set_size + new_set.__len__()
        for index, element in enumerate(new_set):
            self.wordlist[element] = math.log(
                (set_size + index + 1) * math.log(new_size))
    def fetch_space_indices(self, sentence):
        loss_list = [  self.wordlist.get(char, 0) for char in sentence  ]
        for i in range(1, loss_list.__len__()):
            loss_list[i] = loss_list[i] + loss_list[i - 1]
        loss_list = loss_list + [ 9e999 ]
        inde_list = [ 0 ] * loss_list.__len__()
        for i in range(1, loss_list.__len__()):
            for j in (  (i - k) for k in range(1, i + 1)  ):
                loss_prev = loss_list[j]
                loss_next = self.wordlist.get(sentence[ j : i ], 9e999)
                loss = loss_prev + loss_next
                if (loss < loss_list[i]):
                    loss_list[i] = loss
                    inde_list[i] = j
        indices = []
        index = inde_list.__len__() - 1
        while True:
            indices.append(index)
            if (index == 0):
                break
            index = inde_list[index]
        indices = list(reversed(indices))
        return indices
    def sentence_to_list(self, sentence, space_indices):
        sentence_list = [
            sentence[space_indices[i] : space_indices[i + 1]] 
                for i in range(space_indices.__len__() - 1)
        ]
        return sentence_list
    def find_sentence_substrings(self, sentence):
        indices = self.fetch_space_indices(sentence.lower())
        sentence_list = self.sentence_to_list(sentence, indices)
        return sentence_list
    def write_spaces_into_sentence(self, sentence, space_indices):
        new_sentence = " ".join(self.sentence_to_list(sentence, space_indices))
        return new_sentence
    def infer_sentence_spaces(self, sentence):
        new_sentence = self.write_spaces_into_sentence(
            sentence, self.fetch_space_indices(sentence.lower()))
        return new_sentence
class ProfanityDetector:
    def __init__(self, profanity_vocabulary_file = "./profanity.txt"):
        self.profanity_set = set(word.lower() for word 
            in open(profanity_vocabulary_file, "r").read().split("\n")
        )
    def is_profaning(self, word):
        if (word.lower() in self.profanity_set):
            return True
        return False
    def contains_profanity(self, sentence):
        substrings = []
        for i in range(1, sentence.__len__() + 1):
            for j in range(1, i + 1):
                substrings.append(sentence[ i - j : i ])
        return any(self.is_profaning(x) for x in substrings)
class SentenceCleanser:
    def __init__(self, custom_vocabulary_file = "./custom_set.file"):
        self.vocabulary_set = set(word.lower() for word 
            in pickle.load(open(custom_vocabulary_file, 'rb'))
        )
        self.space_inferrer = SpaceInferrer()
        self.profanity_detector = ProfanityDetector()
        self.vocabulary_set = self.vocabulary_set.union(
            self.profanity_detector.profanity_set)
        self.space_inferrer.union_with(self.vocabulary_set)
    def separate_by_number(self, sentence):
        return (
            re.findall("[a-zA-Z\+\#]+", sentence) + 
            re.findall("[0-9]+", sentence)
        )
        
    def rec_cleanse(self, word_list):
        _word_list = [];  profaning = False
        for word in word_list:
            if word.lower() in self.vocabulary_set:
                _word_list.append(word)
                if self.profanity_detector.is_profaning(word):
                    profaning = True
            else:
                __word_list = self.space_inferrer.find_sentence_substrings(word)
                if (__word_list.__len__() == 1):
                    if any(  char.isnumeric() for char in __word_list[0]  ):
                        __word_list = self.separate_by_number(__word_list[0])
                if (__word_list.__len__() > 1):
                    __word_list, _profaning = self.rec_cleanse(__word_list)
                    profaning = profaning or _profaning                    
                _word_list += __word_list
        return _word_list, profaning 
    
    def cleanse(self, sentence):
        return self.rec_cleanse(
            re.findall("[a-zA-Z0-9\+\#]+", sentence))

identifier = LanguageIdentifier.from_modelstring(model, norm_probs = True)
    
comsci_predictor = models.load_model("./models/comsci_model.h5")

def translate(string):
    
    detect  = identifier.classify(string)
    success = True
    
    print("\n\nLANGUAGE DETECTED: {}\n\n".format(detect))
    
    if ((detect[0] != "en") or (detect[1] < 0.95)):
        try:
            url = "http://translate.google.cn/translate_a/single?client=gtx&dt=t&dj=1&ie=UTF-8&sl={}&tl=en&q={}".format(detect[0], string)
            target = json.loads(requests.get(url).text)
            string = " ".join(  target["sentences"][i]["trans"] for i in range(target["sentences"].__len__())  )
            print("\n\nTRANSLATION SUCCESS - TRANSLATED {} -> {}\n\n".format(  detect[0], "en"  ))
        except:
            print("\n\nNETWORK ERROR - CANNOT TRANSLATE NON-ENGLISH SENTENCE\n\n")
            success = False
    else:
        print("\n\nSENTENCE IS IN ENGLISH - USING ORIGINAL SENTENCE\n\n")
    print("\n\nRETURNING SENTENCE: {}\n\n".format(string))
    
    return (string, success)

if (__name__ == "__main__"):
    sentence_cleanser = SentenceCleanser()
    sentence = "ToreadaPDFfileyoumustfirstinstallAdobeFlashReader"
    cleansed = sentence_cleanser.cleanse(sentence)
    print("<{:1}> {}".format(cleansed[1] * 1, " ".join(cleansed[0])))