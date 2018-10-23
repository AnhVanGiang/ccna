from bs4 import BeautifulSoup as BS
import requests
from nltk import word_tokenize, pos_tag
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from statistics import mean

site = 'https://ccnav6.com/ccna-1-introduction-to-networks-v5-1-v6-0-exams-answers-2017'

soup = BS(requests.get(site).content, 'lxml')

dic = {}

all_chap = [c['href'] for c in soup.findAll('a', {'style': 'color: #008000;'})
            if c.text.strip()[-1] in [str(i) for i in range(1, 12)]]


def get_cosine_sim(*strs):
    vectors = [t for t in get_vectors(*strs)]
    return cosine_similarity(vectors)[0][1]


def get_vectors(*strs):
    try:
        text = [t for t in strs]
        vectorizer = CountVectorizer(text)
        vectorizer.fit(text)
        return vectorizer.transform(text).toarray()
    except ValueError:
        return [[0, 0],
                [0,0]]


def extract_nouns(strng):
    nouns = ' '.join([word for word, pos in pos_tag(word_tokenize(strng)) if pos.startswith('NN')])
    if nouns == '':
        return 'empty'
    return nouns


def questions_answers_sim(quest, answ):
    lst1 = []
    lst2 = []
    for i in answ:
        lst1.append(get_cosine_sim(extract_nouns(quest), extract_nouns(i)))
        lst2.append(get_cosine_sim(quest, i))
    return mean([mean(lst1), mean(lst2)])


def compare_answers(lst1, lst2):
    averages_sen = []
    averages_noun = []
    while len(lst1) != len(lst2):
        if len(lst1) < len(lst2):
            lst1.append(' ')
        else:
            lst2.append(' ')
    for i1, i2 in zip(lst1, lst2):
        averages_sen.append(get_cosine_sim(i1, i2))
        averages_noun.append(get_cosine_sim(extract_nouns(i1), extract_nouns(i2)))
    return mean([mean(averages_noun), mean(averages_sen)])


def generate_lst(answers):
    return answers.strip(' ').split(',')


print('Getting content from chapters...')


for chap in all_chap:
    cont_chap = BS(requests.get(chap).content, 'lxml')
    q_content = cont_chap.findAll('ol')
    for ol in q_content:
        for ans in ol.findAll('ul'):
            try:
                dic[ans.find_previous_sibling('strong').text.strip('\n')] = {'answer': [answer.text for answer in ans.findAll('strong')
                                                                             if 'span' in [p1.name for p1 in answer.parents]],
                                                                             'all answer': [answer.text for answer in ans.findAll('li')]}

            except AttributeError:
               continue
        for match_ans in ol.findAll('li'):
            try:
                for l in match_ans.children:
                    if l.text.startswith('Match'):
                        lst = l.find_next_siblings('strong')
                        ans_ = []
                        for ans1, ans2 in zip(lst[:len(lst) - 1:2], lst[1::2]):
                            ans_.append(ans1.text.strip() + ans2.text.strip())
                        dic[l.text.strip('\n')] = ans_

                #dic[match_ans.find_previous_sibling().text.strip()] = [answer_.text for answer_ in match_ans.findAll('span')
                                                                     #if 'strong' in [p1.name for p1 in answer_.parents]]
            except AttributeError:
                continue


print('Finished creating a dictionary...')


if __name__ == '__main__':
    while True:
        question = input('Give me a question: ').strip('\n')
        try:
            answer = dic[question]['answer']
            print('The exact answer is ', answer)
        except KeyError:
            ratios = {}
            count1 = 0
            for k in dic.keys():
                nouns_q = extract_nouns(question)
                cos_nouns = get_cosine_sim(nouns_q, k)
                cos_sent = get_cosine_sim(question, k)
                ratios[k] = {'nouns similarity': cos_nouns, 'sentence similarity': cos_sent, 'average': (cos_sent + cos_nouns)/2}
                if ratios[k]['average'] > 0.5:
                    count1 += 1
            if count1 >= 1:
                print('Exact question not found, possible answers are:')
                for k in dic.keys():
                    if ratios[k]['average'] > 0.5:
                        print(k, '\n', dic[k]['answer'])
                        print(ratios[k])
            else:
                count2 = 0
                print('No similar questions found')
                pos_answers = generate_lst(input('Please input all possible answers:'))
                ratios2 = {}
                for k1 in dic.keys():
                    try:
                        ratios2[k1] = compare_answers(pos_answers, dic[k1]['all answer'])
                        if ratios2[k1] > 0.5:
                            count2 += 1
                    except TypeError:
                        continue
                if count2 >= 1:
                    print('Found question with similar answers:')
                    for k2 in dic.keys():
                        try:
                            if ratios2[k2] > 0.5:
                                print('Question:', k2)
                                print('All answers:', dic[k2]['all answer'])
                                print('Right answers:', dic[k2]['answer'])
                        except KeyError:
                            continue
                else:
                    count3 = 0
                    print('No similar answers found, checking for answers in questions')
                    ratios3 = {}
                    for k3 in dic.keys():
                        try:
                            ratios3[k3] = questions_answers_sim(k3, pos_answers)
                            if questions_answers_sim(k3, pos_answers) > 0.5:
                                count3 += 1
                        except TypeError or ValueError:
                            continue
                    if count3 >= 1:
                        for k4 in dic.keys():
                            if ratios3[k4] > 0.5:
                                print('Results found:')
                                print('Question:', k4)
                                print('Answers:', dic[k4]['answer'])
