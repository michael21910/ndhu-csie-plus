import tensorflow as tf
import tensorflow_hub as hub
import tensorflow_text as text
import numpy
class BertEmbedder:
    def __init__(self):
        self.bert_encoder      = hub.KerasLayer("./pretrained_models/bert_en_uncased_L-12_H-768_A-12_4/")
        self.bert_preprocessor = hub.KerasLayer("./pretrained_models/bert_en_uncased_preprocess_3/")
    def embed_sentence(self, sentence):
        return numpy.array(self.bert_encoder(self.bert_preprocessor([sentence]))["sequence_output"][0])
    def embed_sentences(self, sentence_list):
        return numpy.stack([
            numpy.transpose(vector) for vector in self.bert_encoder(self.bert_preprocessor(sentence_list))["sequence_output"]    
        ])
if (__name__ == "__main__"):
    my_sentence = "Python is a programming language not a snake."
    my_sentence2 = "Rats are pythons' favorite food."
    embedder = BertEmbedder()
    print(embedder.embed_sentence(my_sentence).shape)
    print(embedder.embed_sentence(my_sentence2).shape)