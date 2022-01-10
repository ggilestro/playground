#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  wordle_modeller.py
#  
#  Copyright 2022 Giorgio F. Gilestro <gg@jenner>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

# uses https://github.com/dwyl/english-words/blob/master/words_alpha.txt as wordlist

import random

from operator import and_, or_, contains
from functools import reduce

import numpy as np

class wordle_solver:

    def __init__(self, dict_file = "words_alpha.txt", word_length=5, common_words=20):
        
        self._refresh_dictionary(dict_file, word_length)
        self.common_words = self.frequency_rank(limit=common_words)

    def _refresh_dictionary (self, dict_file, word_length):
        self._dictionary = self.get_words(dict_file, word_length)
        print ('Loaded dictionary with %s words' % len(self._dictionary))
        

    def get_words(self, dict_file, word_length):
        '''
        select words by length from a complete dictionary
        '''
        with open(dict_file) as df:
            all_words = df.readlines()
        
        words = [word.strip().upper() for word in all_words if (len(word.strip()) == 5)]
        
        return words

    def containsAll(self, word, letters):
        return reduce(and_, map(contains, len(letters)*[word], letters))

    def containsAny(self, word, letters):
        return reduce(or_, map(contains, len(letters)*[word], letters))
        
    def hasRepeatingCharacters(self, word):
        return len(set(word)) != len(word)

    def pick_random_word(self, wordlist=None, has_letters=None, hasnot_letters=None, pattern=None, verbose=False, norepeats=False):
        '''
        picks a random word from the dictionary
        the word must contain the letters provided in has
        and must not contain the letters provided in hasnot
        and must match the provided pattern where 
            uppercase letter means same letter, same position
            lowercase letter means same letter, different position
            _ means letter not present
        '''
        
        if has_letters:
            has_letters = "".join(set(has_letters.upper())) 
        
        if hasnot_letters:
            hasnot_letters = "".join(set(hasnot_letters.upper())) 
        
        if wordlist == None:
            wordlist = self._dictionary.copy()
        
        continue_search = has = hasnot = matches = hasrepeats = True
        i = 0

        if verbose: print ('Looking for word that has: %s and hasnot %s with pattern %s' % (has_letters, hasnot_letters, pattern))

        while continue_search:
            try:
                rw = random.choice(wordlist)
                wordlist.remove(rw)
            except:
                #no word match these requirements
                return ''
            
            i += 1
            txt = ''

            if has_letters:
                has = self.containsAll(rw, has_letters)
                txt += ' contains all letters in %s' % has_letters.upper()
                
            if hasnot_letters:
                hasnot = not self.containsAny(rw, hasnot_letters.upper())
                txt += ' does not contain any letter in %s' % hasnot_letters.upper()

            if pattern:
                m1 = all ([(c[0].upper() == c[1].upper()) for c in zip(pattern, rw) if c[0].isupper()])
                m2 = all ([((c[0].upper() != c[1].upper()) and (c[0].upper() in rw)) for c in zip(pattern, rw) if c[0].islower()])
                matches = m1 and m2
                txt += ' matches tha pattern %s' % pattern
                
            continue_search = (has == False) or (hasnot == False) or (matches == False)
            if norepeats:
                continue_search = self.hasRepeatingCharacters(rw)


        if verbose: print (rw + txt + ' found in %s attempts' % i)
        return rw

    def analyse_frequency(self, wordlist = None):
        '''
        Analyse the frequency of letters in the given dictionary
        '''

        if wordlist == None:
            wordlist = self._dictionary
        
        distribution = {}
        for word in wordlist:
            for letter in word.strip():
                try:
                    distribution[letter] += 1
                except:
                    distribution.update({letter : 1})
                    
        return dict(sorted(distribution.items(), key=lambda item: item[1], reverse=False))


    def compare_words(self, guess, word):
        '''
        Play a round
        '''
        guess = guess.upper()
        word = word.upper()
        result = {
                  'word' : guess,
                  'green' : '',
                  'yellow': '',
                  'grey'  : '',
                  'pattern'  : '',
                  'score' : 0,
                  'solved' : (guess == word)
                  }
        
        if len(guess) != len(word):
            return result
        
        
        for i in range(len(guess)):
            if (guess[i] == word[i]):
                result['green'] += guess[i]
                result['pattern'] += guess[i].upper()
                result['score'] += 5
                
            elif (guess[i] in word):
                result['yellow'] += guess[i]
                result['pattern'] += guess[i].lower()
                result['score'] += 1
                
            else:
                result['grey'] += guess[i]
                result['pattern'] += '_'
            
        return result

    def check_rank (self, word, wordllist=None):
        '''
        Check how the word ranks on the wordlist
        '''
        allwords = self.frequency_rank(limit=None, descending=True)
        rank = {k:i for i,k in enumerate(allwords.keys())}
        
        try:
            return { word.upper(): rank[word.upper()], 'total' : len(rank) }
        except:
            return { word.upper(): 'not found', 'total' : len(allwords) }

    def frequency_rank(self, wordlist=None, limit=50, descending=True):
        
        from itertools import islice

        def _take(n, iterable):
            "Return first n items of the iterable as a list"
            return list(islice(iterable, n))
        
        fr = self.analyse_frequency(wordlist)
        result = {}
        
        if wordlist == None:
            wordlist = self._dictionary

        if limit:
            wordlist = [word for word in wordlist if not self.hasRepeatingCharacters(word)]

        for word in wordlist:
            score = 0
            for letter in word.strip():
                score += fr[letter]
            result[word.strip().upper()] = score

        sorted_result = dict(sorted(result.items(), key=lambda item: item[1], reverse=descending))
        
        if limit:
            return _take(limit, sorted_result.keys())
        else:
            return sorted_result

    def solve (self, guess_word=None, use_smart=True, stupid_mode=False, attempts=6, exclude=0):
        '''
        Solve a single game
        '''
        
        game = []
        has = ''
        hasnot = ''
        stuck = 0

        if guess_word == None:
            p = self.pick_random_word()
        else:
            p = guess_word

        if use_smart:
            #use a smart word at the beginning then refine starting from there
            first_attempt = random.choice(self.common_words)
        else:
            #use a random word at the beginning
            first_attempt = self.pick_random_word()
            
        r = self.compare_words (first_attempt, p)
        has += r['yellow'] + r['green']
        hasnot += r['grey']
        game.append((r['word'], r['pattern']))

        if r['solved']: return {'game': game, 'solved' : True, 'word' : p, 'attempts' : len(game)}
            
        #explore for N times a word that does not have any of the letters we found so far
        for a in range(exclude):
            tw = self.pick_random_word (hasnot_letters=hasnot+has, norepeats=True)
            if tw == '': stuck += 1
                

            r = self.compare_words(tw, p)
            has += r['yellow'] + r['green']
            hasnot += r['grey']
            game.append((r['word'], r['pattern']))
            
            if r['solved']: return {'game': game, 'solved' : True, 'word' : p, 'attempts' : len(game)}

        if not stupid_mode:
            #for the remaining attempts try to guess using the information gathered so far
            for a in range(attempts-(exclude+1)):
                r = self.compare_words(self.pick_random_word (pattern=r['pattern'], hasnot_letters=hasnot, has_letters=has), p)
                has += r['yellow'] + r['green']
                hasnot += r['grey']
                game.append((r['word'], r['pattern']))

                if r['solved']: return {'game': game, 'solved' : True, 'word' : p, 'attempts' : len(game)}
        else:
            #or use stupid mode that will simply try random words
            for a in range(attempts-(exclude+1)):
                r = self.compare_words(self.pick_random_word(), p)
                has += r['yellow'] + r['green']
                hasnot += r['grey']
                game.append((r['word'], r['pattern']))

                if r['solved']: return {'game': game, 'solved' : True, 'word' : p, 'attempts' : len(game)}
            

        return {'game': game, 'solved' : False, 'word' : p, 'attempts' : attempts+1}

    def solve_many (self, guess_word=None, use_smart=True, stupid_mode=False, N_GAMES=100, attempts=6, exclude=0):

        score = 0
        stuck = 0
        win = []

        for i in range(N_GAMES):
            r = self.solve(guess_word, use_smart, stupid_mode, attempts, exclude)
            score += r['solved']
            win.append (r['attempts'])
            print ('Game %s, word %s, solved in:%s \r' % (i, r['word'], r['attempts']), end="")

        return {'success_rate' : score / N_GAMES, 'stuck' : stuck, 'profile' : np.array(win)}

if __name__ == '__main__':

    g = wordle_solver('full_five_letters_words.txt')
    print (g.solve(guess_word=None, use_smart=True, exclude=2))
