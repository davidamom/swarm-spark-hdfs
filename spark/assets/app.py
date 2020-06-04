
# -*- coding: utf-8 -*-

""" ❤️ Made with love by DIRAG - TAILABS"""

import sys
import logging
import uuid
from pyspark import (
    SparkContext,
    SparkConf
)

if __name__ == '__main__':
    
    """ Criar SparkContext """
    conf = SparkConf().setAppName('Conta palavras').setMaster('spark://spark-master:7077')
    sc = SparkContext(conf = conf)

    """ Carregar o arquivo """
    palavras = sc.textFile('hdfs://primary-namenode/alice.txt').flatMap(lambda line: line.split(' '))

    """ Conta a ocorrência de palavras """
    contagem = palavras.map(lambda palavra: (palavra, 1)).reduceByKey(lambda a, b: a + b)

    """ Salvar o resultado """
    contagem.saveAsTextFile(''.join(['hdfs://primary-namenode', '/tmp/saida_contagem.txt', ]))

