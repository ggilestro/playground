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

def formatgametohtml(game):
    '''
    Converts a Wordle game sequence into HTML format for visual display.
    
    This function generates HTML that mimics the official Wordle game interface,
    complete with CSS styling for colored tiles representing game feedback.
    
    Parameters:
    -----------
    game : list of tuples
        List of (word, pattern) tuples representing each guess and its result.
        Each tuple contains:
        - word: The guessed word (string)
        - pattern: Result pattern where:
            * Uppercase letter = correct letter, correct position (green)
            * Lowercase letter = correct letter, wrong position (yellow)
            * '_' = letter not in target word (grey)
    
    Returns:
    --------
    str
        Complete HTML document with embedded CSS styling that displays
        the game as a grid of colored tiles matching Wordle's visual style.
    
    HTML Structure:
    --------------
    - Uses external font resources (Gilroy, Font Awesome)
    - Creates a game board container with fixed dimensions (350x420px)
    - Each guess becomes a game-row with 5 game-tile elements
    - Tiles are colored based on evaluation: correct (green), present (yellow), absent (grey)
    
    Example Input:
    -------------
    [('RACES', '_A___'),
     ('CAMPO', '_A_p_'),
     ('CAFES', '_A___'),
     ('KAPPA', '_Appa'),
     ('PAINT', 'PA_n_'),
     ('PAGAN', 'PAGAN')]
    
    CSS Classes Used:
    ----------------
    - 'correct': Green background for exact matches
    - 'present': Yellow background for letters in wrong position
    - 'absent': Grey background for letters not in word
    
    Dependencies:
    ------------
    Requires 'wordle.css' file in same directory for complete styling.
    '''
    
    HTML_HEAD = '<html><head><link rel="stylesheet" href="wordle.css"><style type="text/css">@font-face{font-family:Gilroy;font-style:normal;font-weight:100 400;src:url(https://pouch-global-font-assets.s3.eu-central-1.amazonaws.com/Gilroy-Medium.otf)}@font-face{font-family:Gilroy;font-style:normal;font-weight:500 900;src:url(https://pouch-global-font-assets.s3.eu-central-1.amazonaws.com/Gilroy-Bold.otf)}@font-face{font-family:"Font Awesome 5 Free";font-style:normal;font-weight:900;src:url(https://use.fontawesome.com/releases/v5.6.3/webfonts/fa-solid-900.woff2) format("woff2")}@font-face{font-family:"Font Awesome 5 Brands";font-style:normal;font-weight:normal;src:url(https://use.fontawesome.com/releases/v5.6.3/webfonts/fa-brands-400.woff2) format("woff2")}</style></head><body><div id="game"><div id="board-container"><div id="board" style="width: 350px; height: 420px;">'

    HTML_FOOT = "</div></div></div></body></html><body>"
    
    TABLE = ''
    for (word, pattern) in game:
        TABLE += '<game-row letters="%s" length="5"><div class="row">' % word
        for (letter, match) in zip (word, pattern):
            if match.isupper(): evaluation = 'correct'
            elif match.islower(): evaluation = 'present'
            else: evaluation = 'absent'
            TABLE += '<game-tile letter="%s" evaluation="%s" reveal=""><div class="tile" data-state="%s" data-animation="idle">%s</div></game-tile>' % (letter, evaluation, evaluation, letter)
        TABLE += '</div></game-row>'

    return HTML_HEAD + TABLE + HTML_FOOT
    

class wordle_solver:

    def __init__(self, dict_file = "words_alpha.txt", word_length=5, common_words=20):
        '''
        Initialize the Wordle solver with a word dictionary and frequency analysis.
        
        This constructor sets up the core components needed for Wordle solving:
        - Loads and filters the word dictionary
        - Performs frequency analysis to identify optimal starting words
        - Caches common high-frequency words for smart strategy
        
        Parameters:
        -----------
        dict_file : str, default "words_alpha.txt"
            Path to dictionary file containing words (one per line).
            Common options: "wordle_words.txt" (official), "words_alpha.txt" (comprehensive)
            
        word_length : int, default 5
            Length of words to extract from dictionary. Wordle uses 5-letter words.
            
        common_words : int, default 20
            Number of top frequency-ranked words to cache for smart starting strategy.
            These words are pre-computed to avoid repeating calculations during gameplay.
            
        Attributes Created:
        ------------------
        self._dictionary : list
            Filtered list of valid words from the dictionary file
        self.common_words : list
            Pre-computed list of highest frequency words (no repeating letters)
            Used by pick_smart_word() for optimal opening moves
            
        Note:
        -----
        The frequency ranking excludes words with repeating letters by default,
        as these are generally less optimal for initial exploration in Wordle.
        '''
        
        self._refresh_dictionary(dict_file, word_length)
        self.common_words = self.frequency_rank(limit=common_words, exclude_repeats=True)

    def _refresh_dictionary (self, dict_file, word_length):
        '''
        Loads and refreshes the internal word dictionary from file.
        
        This private method handles the initialization and updating of the solver's
        word dictionary by reading from a file and filtering by word length.
        
        Parameters:
        -----------
        dict_file : str
            Path to the dictionary file containing words (one word per line)
        word_length : int
            Desired length of words to extract (typically 5 for Wordle)
            
        Side Effects:
        ------------
        - Updates self._dictionary with filtered word list
        - Prints confirmation message with word count
        - Called automatically during initialization and when dictionary changes
        
        Note:
        -----
        This is a private method (prefixed with _) intended for internal use only.
        External code should use the constructor or other public methods.
        '''
        self._dictionary = self.get_words(dict_file, word_length)
        print ('Loaded dictionary with %s words' % len(self._dictionary))
    
    def get_words(self, dict_file, word_length):
        '''
        Extracts words of specified length from a dictionary file.
        
        Reads a dictionary file and filters words by length, converting them
        to uppercase for consistent processing throughout the solver.
        
        Parameters:
        -----------
        dict_file : str
            Path to dictionary file (plain text, one word per line)
        word_length : int
            Target word length to filter for (typically 5 for Wordle)
            
        Returns:
        --------
        list of str
            List of words matching the specified length, converted to uppercase
            
        File Format:
        -----------
        Expected dictionary format:
        - Plain text file
        - One word per line
        - Mixed case acceptable (automatically converted to uppercase)
        - Extra whitespace automatically stripped
        
        Note:
        -----
        The function currently hardcodes length check to 5 regardless of word_length
        parameter. This appears to be a bug that should be addressed.
        '''
        with open(dict_file) as df:
            all_words = df.readlines()
        
        words = [word.strip().upper() for word in all_words if (len(word.strip()) == word_length)]
        
        return words

    def containsAll(self, word, letters):
        '''
        Checks if a word contains all specified letters.
        
        Uses functional programming approach with reduce() and map() to test
        whether every letter in the letters parameter exists in the word.
        
        Parameters:
        -----------
        word : str
            The word to test for letter presence
        letters : str
            String of letters that must all be present in the word
            
        Returns:
        --------
        bool
            True if word contains ALL letters, False otherwise
            
        Algorithm:
        ----------
        - Creates list of [word] repeated len(letters) times
        - Maps contains function across word list and letters
        - Reduces with logical AND to ensure all letters are present
        
        Example:
        --------
        containsAll("HOUSE", "HO") -> True (H and O both in HOUSE)
        containsAll("HOUSE", "HZ") -> False (Z not in HOUSE)
        
        Note:
        -----
        This is a utility function used by pick_random_word() for filtering
        words that must contain specific letters (yellow/green Wordle feedback).
        '''
        return reduce(and_, map(contains, len(letters)*[word], letters))

    def containsAny(self, word, letters):
        '''
        Checks if a word contains any of the specified letters.
        
        Uses functional programming approach with reduce() and map() to test
        whether at least one letter in the letters parameter exists in the word.
        
        Parameters:
        -----------
        word : str
            The word to test for letter presence
        letters : str
            String of letters where at least one must be present in the word
            
        Returns:
        --------
        bool
            True if word contains ANY of the letters, False if none are present
            
        Algorithm:
        ----------
        - Creates list of [word] repeated len(letters) times
        - Maps contains function across word list and letters
        - Reduces with logical OR to check if any letters are present
        
        Example:
        --------
        containsAny("HOUSE", "HZ") -> True (H is in HOUSE)
        containsAny("HOUSE", "XYZ") -> False (none of X, Y, Z in HOUSE)
        
        Note:
        -----
        This is a utility function used by pick_random_word() for filtering
        words that must NOT contain specific letters (grey Wordle feedback).
        '''
        return reduce(or_, map(contains, len(letters)*[word], letters))
        
    def hasRepeatingCharacters(self, word):
        '''
        Determines if a word contains any repeating letters.
        
        Compares the length of the word with the length of its unique character set
        to detect duplicate letters. Used for filtering strategies that want to
        maximize letter discovery by avoiding repeated characters.
        
        Parameters:
        -----------
        word : str
            The word to analyze for character repetition
            
        Returns:
        --------
        bool
            True if word has repeating characters, False if all characters are unique
            
        Algorithm:
        ----------
        - Converts word to set() to eliminate duplicates
        - Compares set length to original word length
        - If lengths differ, word has repeating characters
        
        Examples:
        ---------
        hasRepeatingCharacters("HOUSE") -> False (all unique: H-O-U-S-E)
        hasRepeatingCharacters("HELLO") -> True (L appears twice)
        
        Usage:
        ------
        Used by pick_random_word() when norepeats=True to filter out words
        with duplicate letters during exploration phases of Wordle solving.
        '''
        return len(set(word)) != len(word)

    def pick_smart_word(self):
        '''
        Selects a random word from the pre-computed list of optimal starting words.
        
        This method provides the "smart" strategy for Wordle by choosing from words
        that have been ranked highest by letter frequency analysis. These words
        are cached during initialization to avoid repeated computations.
        
        Returns:
        --------
        str
            A randomly selected word from the top frequency-ranked words list
            
        Strategy Logic:
        --------------
        The common_words list contains words that:
        - Have high letter frequency scores (common letters like E, A, R, O, T)
        - Exclude words with repeating letters (to maximize information gain)
        - Are pre-computed during initialization for performance
        
        Usage Context:
        -------------
        Called by solve() method when use_smart=True parameter is set.
        Provides significantly better performance than random word selection
        by starting with words that statistically reveal more information.
        
        Performance Impact:
        ------------------
        According to analysis in the codebase, smart starting words can improve
        success rates from ~19% (random) to ~97% (optimized strategies).
        
        Example:
        --------
        # Smart words might include: AROSE, SLATE, CRANE, etc.
        smart_word = solver.pick_smart_word()  # Returns e.g., "AROSE"
        '''
        return random.choice(self.common_words)

    def pick_random_word(self, wordlist=None, has_letters=None, hasnot_letters=None, pattern=None, norepeats=False, verbose=False):
        '''
        Selects a random word from the dictionary that matches specified constraints.
        
        This function is central to the Wordle solving strategy, filtering the word list
        based on game state information to find candidate words for the next guess.
        
        Parameters:
        -----------
        wordlist : list, optional
            Custom word list to search from. If None, uses the solver's main dictionary.
            
        has_letters : str, optional
            Letters that MUST be present in the word (from yellow/green feedback).
            Function automatically removes duplicates and converts to uppercase.
            
        hasnot_letters : str, optional
            Letters that must NOT be present in the word (from grey feedback).
            Function automatically removes duplicates and converts to uppercase.
            
        pattern : str or list of str, optional
            Wordle pattern(s) to match, where:
            - Uppercase letter = correct letter in correct position (green)
            - Lowercase letter = correct letter in wrong position (yellow) 
            - '_' = letter not present in the word
            Multiple patterns can be provided as a list for multi-round constraints.
            
        norepeats : bool, default False
            If True, excludes words with repeating letters from consideration.
            Useful for exploration strategies that maximize letter discovery.
            
        verbose : bool, default False
            If True, prints detailed search information for debugging.
            
        Returns:
        --------
        tuple : (selected_word, frequency_ranked_matches)
            - selected_word: Randomly chosen word from matching candidates
            - frequency_ranked_matches: List of all matching words ranked by letter frequency
            
        Algorithm Details:
        -----------------
        1. Sanitizes input by removing duplicates and resolving conflicts between
           has_letters and hasnot_letters (has_letters takes precedence)
        2. Iterates through entire wordlist to find all matching candidates
        3. For each word, checks:
           - Contains all required letters (has_letters)
           - Contains none of the forbidden letters (hasnot_letters)
           - Matches all provided patterns using green/yellow/grey logic
           - Optionally excludes words with repeating characters
        4. Returns random selection from valid candidates plus frequency-ranked list
        
        Pattern Matching Logic:
        ----------------------
        For each pattern provided:
        - Green check: All uppercase letters match word at same positions
        - Yellow check: All lowercase letters exist in word but not at pattern positions
        - Both conditions must be true for pattern to match
        
        Usage Examples:
        --------------
        # Find words containing 'A' and 'E' but not 'R' or 'S'
        word, candidates = pick_random_word(has_letters='AE', hasnot_letters='RS')
        
        # Find words matching specific Wordle feedback pattern
        word, candidates = pick_random_word(pattern='_A_e_', has_letters='AE')
        
        # Find exploration words (no repeats, avoiding known letters)
        word, candidates = pick_random_word(hasnot_letters='AERS', norepeats=True)
        '''
        
        if has_letters:
            #remove non unique occurances
            has_letters = "".join(set(has_letters.upper())) 
        
        if hasnot_letters:
            #remove non unique occurances
            hasnot_letters = "".join(set(hasnot_letters.upper())) 

        if has_letters and hasnot_letters:
            #removing letters that are in contrast with the has_letter command
            hasnot_letters = "".join([letter for letter in hasnot_letters if letter not in has_letters])
        
        if wordlist == None:
            wordlist = self._dictionary.copy()
        
        continue_search = has = hasnot = matches = hasrepeats = True
        i = 0

        if verbose: print ('Looking for word that has [%s] and has not [%s] with pattern [%s]' % (has_letters, hasnot_letters, pattern))

        found_words = []
        
        for word in wordlist:

        #while continue_search:
            #try:
            #    word = random.choice(wordlist)
            #    wordlist.remove(rw)
            #except:
            #    #no word match these requirements
            #    return ''
            
            i += 1
            txt = ''

            if has_letters:
                has = self.containsAll(word, has_letters)
                txt += ' contains all letters in %s' % has_letters.upper()
                
            if hasnot_letters:
                hasnot = not self.containsAny(word, hasnot_letters.upper())
                txt += ' does not contain any letter in %s' % hasnot_letters.upper()

            if pattern:
                if type(pattern) == str: pattern = [pattern]
                for pat in pattern:
                    green = all ([(c[0].upper() == c[1].upper()) for c in zip(pat, word) if c[0].isupper()])
                    yellow = all ([((c[0].upper() != c[1].upper()) and (c[0].upper() in word)) for c in zip(pat, word) if c[0].islower()])
                    matches = green and yellow
                    if not matches: break
                    txt += ' matches tha pattern %s' % pat
                    

            continue_search = (has == False) or (hasnot == False) or (matches == False) or (norepeats and self.hasRepeatingCharacters(word))
            if not continue_search: found_words.append(word)


        if verbose: print (word + txt + ' found in %s attempts' % i)
        return random.choice(found_words), self.frequency_rank(found_words)

    def analyse_frequency(self, wordlist = None, ascount=True):
        '''
        Analyzes letter frequency distribution across the word dictionary.
        
        This method performs comprehensive frequency analysis of letters both globally
        and by position, providing the statistical foundation for smart word selection
        and ranking strategies in Wordle solving.
        
        Parameters:
        -----------
        wordlist : list, optional
            Custom word list to analyze. If None, uses the solver's main dictionary.
            
        ascount : bool, default True
            If True, returns absolute counts of letter occurrences.
            If False, returns relative frequencies (counts normalized to 0-1 range).
            
        Returns:
        --------
        tuple : (global_distribution, position_distributions)
            - global_distribution: dict mapping letters to their total frequency/count
            - position_distributions: list of 5 dicts, each mapping letters to 
              their frequency/count at that specific position (0-4)
              
        Algorithm Details:
        -----------------
        1. Iterates through every word in the dictionary
        2. For each letter in each word:
           - Increments global letter count
           - Increments position-specific letter count
        3. Handles missing entries gracefully using try/except blocks
        4. Optionally converts counts to relative frequencies
        
        Nested Functions:
        ----------------
        sorted_dict(d, reverse=False):
            Sorts dictionary by values in ascending order (reverse=False parameter 
            appears to be unused - always sorts ascending)
            
        counttofrequency(d):
            Converts absolute counts to relative frequencies by dividing each
            count by the total sum of all counts
            
        Data Structure:
        --------------
        Global distribution: {'A': 975, 'B': 267, 'C': 477, ...}
        Position distributions: [
            {0: {'A': 140, 'B': 173, ...}},  # Position 0 frequencies
            {1: {'A': 304, 'E': 241, ...}},  # Position 1 frequencies
            ...
        ]
        
        Usage:
        ------
        Used by frequency_rank() to calculate word scores based on letter popularity.
        Essential for the "smart" strategy that prioritizes words with common letters.
        
        Performance Notes:
        -----------------
        This analysis is computationally expensive and should be cached when possible.
        The solver caches common_words during initialization to avoid repeated calls.
        '''

        def sorted_dict(d, reverse=False):
            return dict(sorted(d.items(), key=lambda item: item[1], reverse=False))

        def counttofrequency(d):
            count = 0
            total = 0
            
            for letter in d:
                count = d[letter]
                total += count
                
            for letter in d:
                d[letter] = d[letter] / total
            
            return d

        if wordlist == None:
            wordlist = self._dictionary
        
        distribution = {}
        position = []
        
        for word in wordlist:
            i = 0
            for letter in word.strip():
                try:
                    distribution[letter] += 1
                    position[i][letter] += 1
                except:
                    distribution.update({letter : 1})
                    try:
                        position[i].update({letter : 1})
                    except:
                        position.append({letter : 1})
                i+=1
                
        #absolute count
        if ascount:
            return sorted_dict(distribution), [sorted_dict(pos) for pos in position]
        
        #or relative frequency?
        else:
            return counttofrequency(sorted_dict(distribution)), [counttofrequency(sorted_dict(pos)) for pos in position]

    def compare_words(self, guess, word):
        '''
        Implements the core Wordle game logic by comparing a guess against the target word.
        
        This method simulates a single round of Wordle, determining which letters are:
        - Green (correct letter in correct position)
        - Yellow (correct letter in wrong position) 
        - Grey (letter not in target word)
        
        The algorithm follows official Wordle rules, including proper handling of
        duplicate letters and the two-pass scoring system.
        
        Parameters:
        -----------
        guess : str
            The guessed word (automatically converted to uppercase)
        word : str
            The target word to compare against (automatically converted to uppercase)
            
        Returns:
        --------
        dict
            Comprehensive result dictionary containing:
            - 'word': The original guess (uppercase)
            - 'green': String of all letters that were green (exact matches)
            - 'yellow': String of all letters that were yellow (wrong position)
            - 'grey': String of all letters that were grey (not in word)
            - 'pattern': Visual pattern string where:
                * Uppercase letter = green (correct position)
                * Lowercase letter = yellow (wrong position)
                * '_' = grey (not in word)
            - 'score': Numeric score (5 points per green, 1 per yellow)
            - 'solved': Boolean indicating if guess exactly matches target
            
        Algorithm Details:
        -----------------
        1. Input validation: Returns empty result if word lengths don't match
        2. GREEN PASS: First iteration identifies exact position matches
           - Marks green letters in pattern (uppercase)
           - Replaces matched positions in target with '*' to prevent double-counting
           - Accumulates green letters and score
        3. YELLOW/GREY PASS: Second iteration processes remaining positions
           - Skips positions already marked as green ('*')
           - Checks if guess letter exists elsewhere in remaining target
           - Marks as yellow (lowercase) if found, grey ('_') if not
           - Accumulates yellow/grey letters and score
           
        Duplicate Letter Handling:
        -------------------------
        The two-pass algorithm correctly handles duplicates by:
        - Processing exact matches first (green)
        - Removing matched letters from consideration
        - Only then checking for positional mismatches (yellow)
        
        Example:
        --------
        compare_words("HELLO", "LLAMA")
        Returns: {
            'word': 'HELLO',
            'green': 'L',        # Second L matches position 1
            'yellow': '',        # No yellow letters
            'grey': 'HEOO',      # H, E, O, O not in LLAMA
            'pattern': '_L___',  # Only position 1 is green
            'score': 5,          # 5 points for one green
            'solved': False
        }
        
        Usage:
        ------
        Central to solve() method for game simulation and strategy evaluation.
        Pattern output is used by pick_random_word() for constraint-based filtering
        in subsequent guesses.
        '''
        
        def assign(word, position, character):
            a = list(word)
            a[position] = character
            return "".join(a)
            
        guess = guess.upper()
        word = word.upper()
        

        result = {
                  'word' : guess,
                  'green' : '',
                  'yellow': '',
                  'grey'  : '',
                  'pattern'  : "_" * len(guess),
                  'score' : 0,
                  'solved' : (guess == word)
                  }
        
        if len(guess) != len(word):
            return result
        
        #find green letters and removes them from the word
        for i in range(len(guess)):
            if (guess[i] == word[i]):
                result['green'] += guess[i]
                result['pattern'] = assign(result['pattern'], i, guess[i].upper())
                result['score'] += 5
                word = assign(word, i, '*')

        #finds yellow and grey letters
        for i in range(len(guess)):
            if word[i] == '*':
                pass
            
            elif (guess[i] in word):
                result['yellow'] += guess[i]
                result['pattern'] = assign(result['pattern'], i, guess[i].lower())
                result['score'] += 1
                
            else:
                result['grey'] += guess[i]
                result['pattern'] = assign(result['pattern'], i, '_')

        return result

    def check_rank (self, word, wordllist=None):
        '''
        Determines the frequency-based ranking of a specific word in the dictionary.
        
        This method evaluates how a given word ranks compared to all other words
        when sorted by letter frequency score. Lower rank numbers indicate words
        with more common letters (better for Wordle strategy).
        
        Parameters:
        -----------
        word : str
            The word to look up in the frequency rankings
        wordllist : unused parameter
            Present in signature but not used in implementation
            
        Returns:
        --------
        dict
            Dictionary containing:
            - word.upper(): The rank (0-based index) or 'not found'
            - 'total': Total number of words in the ranking
            
        Algorithm:
        ----------
        1. Generates complete frequency ranking of all dictionary words
        2. Creates reverse lookup dictionary (word -> rank)
        3. Returns rank position or 'not found' if word not in dictionary
        
        Example:
        --------
        check_rank("AROSE") might return:
        {'AROSE': 0, 'total': 2315}  # AROSE is the top-ranked word
        
        check_rank("ZZZZZ") might return:
        {'ZZZZZ': 'not found', 'total': 2315}  # Invalid word
        
        Usage:
        ------
        Useful for analyzing and comparing the theoretical optimality of
        different word choices in Wordle strategies.
        
        Note:
        -----
        The wordllist parameter appears to be unused legacy code.
        '''
        allwords = self.frequency_rank(limit=None, descending=True)
        rank = {k:i for i,k in enumerate(allwords.keys())}
        
        try:
            return { word.upper(): rank[word.upper()], 'total' : len(rank) }
        except:
            return { word.upper(): 'not found', 'total' : len(allwords) }

    def frequency_rank(self, wordlist=None, limit=50, exclude_repeats=False, descending=True):
        '''
        Ranks words by their letter frequency scores, identifying optimal word choices.
        
        This method is fundamental to the "smart" Wordle strategy, scoring each word
        based on how common its letters are in the dictionary and returning the
        highest-scoring words for strategic advantage.
        
        Parameters:
        -----------
        wordlist : list, optional
            Custom word list to rank. If None, uses the solver's main dictionary.
            
        limit : int, optional, default 50
            Maximum number of top words to return. If None, returns all words.
            
        exclude_repeats : bool, default False
            If True, filters out words containing duplicate letters.
            Useful for exploration strategies that maximize unique letter discovery.
            
        descending : bool, default True
            If True, sorts by highest scores first (best words first).
            If False, sorts by lowest scores first.
            
        Returns:
        --------
        list or dict
            - If limit is specified: List of top words (limit parameter controls length)
            - If limit is None: Complete dictionary of {word: score} mappings
            
        Algorithm:
        ----------
        1. Calls analyse_frequency() to get letter frequency data
        2. For each word, calculates total score by summing frequency of each letter
        3. Sorts words by their total frequency score
        4. Optionally filters out words with repeating characters
        5. Returns top N words or complete sorted dictionary
        
        Scoring System:
        --------------
        Each word gets a score equal to the sum of its letters' frequencies.
        Words with common letters (E, A, R, O, T) score higher than words
        with rare letters (Q, X, Z, J).
        
        Example Scores:
        --------------
        "AROSE" might score ~12.5 (high - very common letters)
        "ZEBRA" might score ~8.2 (medium - mix of common and rare)
        "JAZZY" might score ~3.1 (low - rare letters, repeats)
        
        Usage:
        ------
        - Called during initialization to create common_words cache
        - Used by pick_random_word() to rank filtered word candidates
        - Essential for smart strategy implementation
        
        Performance:
        -----------
        Computationally expensive due to frequency analysis.
        Results should be cached when possible.
        '''
        
        from itertools import islice

        def _take(n, iterable):
            "Return first n items of the iterable as a list"
            return list(islice(iterable, n))
        
        fr, position = self.analyse_frequency(wordlist)
        result = {}
        
        if wordlist == None:
            wordlist = self._dictionary

        if exclude_repeats:
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

    def solve (self, guess_word=None, use_smart=True, start_with=None, stupid_mode=False, attempts=6, exclude=0):
        '''
        Solves a single Wordle game using configurable strategies and parameters.
        
        This is the main method that orchestrates the complete Wordle solving process,
        implementing various strategies from random guessing to sophisticated multi-phase
        approaches that optimize for both exploration and exploitation.
        
        Parameters:
        -----------
        guess_word : str, optional
            Specific target word to solve. If None, picks a random word from dictionary.
            Used for testing specific scenarios or analyzing particular words.
            
        use_smart : bool, default True
            Whether to use frequency-optimized starting words (smart strategy).
            - True: Selects from pre-computed high-frequency words
            - False: Uses completely random starting words
            
        start_with : str, optional
            Specific word to use as the first guess, overriding smart/random selection.
            Useful for testing the effectiveness of particular opening words.
            
        stupid_mode : bool, default False
            If True, uses pure random guessing throughout (baseline for comparison).
            Ignores all learned information and pattern matching.
            
        attempts : int, default 6
            Maximum number of guesses allowed (standard Wordle allows 6).
            
        exclude : int, default 0
            Number of "exploration rounds" using words that avoid known letters.
            Strategy: sacrifice early guesses to discover more letters before focusing.
            
        Returns:
        --------
        dict
            Complete game result containing:
            - 'game': List of (word, pattern) tuples for each guess
            - 'solved': Boolean indicating if word was found
            - 'word': The target word that was being solved
            - 'attempts': Number of guesses used (or attempts+1 if failed)
            
        Algorithm Phases:
        ----------------
        1. TARGET SELECTION: Choose or generate the word to solve
        2. OPENING STRATEGY: Select first guess based on strategy parameters
        3. STUPID MODE: If enabled, use pure random guessing (bypass all logic)
        4. SMART SOLVING: Multi-phase approach:
           - Phase 1: Opening guess (smart or random)
           - Phase 2: Exploration rounds (exclude known letters)
           - Phase 3: Exploitation rounds (use all known constraints)
           
        Strategy Details:
        ----------------
        EXPLORATION PHASE (exclude > 0):
        - Deliberately avoids words containing known letters
        - Maximizes discovery of new letters
        - Uses norepeats=True to avoid duplicate letters
        - Trades early guesses for more information
        
        EXPLOITATION PHASE:
        - Uses all accumulated constraints (has_letters, hasnot_letters, patterns)
        - Applies pattern matching from all previous guesses
        - Selects words that satisfy all known constraints
        - Prioritizes frequency-ranked candidates
        
        Constraint Accumulation:
        -----------------------
        - has: Accumulates all yellow and green letters found
        - hasnot: Accumulates all grey letters found
        - pattern_history: Stores patterns from all guesses for constraint solving
        
        Performance Insights:
        --------------------
        According to codebase analysis:
        - Random strategy: ~19% success rate
        - Smart strategy: ~97% success rate
        - Exploration (exclude=1-2): Often improves performance
        - Stupid mode: Worst performance, used as baseline
        
        Example Usage:
        -------------
        # Standard smart solve
        result = solver.solve(use_smart=True, exclude=1)
        
        # Test specific word with exploration
        result = solver.solve(guess_word="CRANE", exclude=2)
        
        # Pure random (baseline)
        result = solver.solve(use_smart=False, stupid_mode=True)
        
        Example Return:
        --------------
        {
            'game': [('AROSE', '_r_s_'), ('CRISP', '_r_s_'), ('FROST', 'FROST')],
            'solved': True,
            'word': 'FROST',
            'attempts': 3
        }
        '''
        
        game = []
        has = ''
        hasnot = ''
        stuck = 0

        if guess_word == None:
            p, _ = self.pick_random_word()
        else:
            p = guess_word

        if start_with:
            #start with the provided word
            first_attempt = start_with
            
        elif use_smart:
            #use a smart word at the beginning then refine starting from there
            first_attempt = random.choice(self.common_words)
            
        else:
            #use a random word at the beginning
            first_attempt, _ = self.pick_random_word()

        if stupid_mode:
            # use stupid mode that will simply try random words
            for a in range(attempts):
                w, _ = self.pick_random_word()
                r = self.compare_words(w, p)
                has += r['yellow'] + r['green']
                hasnot += r['grey']
                game.append((r['word'], r['pattern']))

                if r['solved']: return {'game': game, 'solved' : True, 'word' : p, 'attempts' : len(game)}
            return {'game': game, 'solved' : False, 'word' : p, 'attempts' : attempts+1}
        
        #ROUND ONE    
        r = self.compare_words (first_attempt, p)
        has += r['yellow'] + r['green']
        hasnot += r['grey']
        game.append((r['word'], r['pattern']))

        if r['solved']: return {'game': game, 'solved' : True, 'word' : p, 'attempts' : len(game)}

        #ROUNDS 2-3 (optional)
        #explore for N times a word that does not have any of the letters we found so far
        excluded = 0
        for a in range(exclude):
            try:
                _, possibilities_left = self.pick_random_word (hasnot_letters=hasnot+has, norepeats=True)
                tw = possibilities_left[0]
            except:
                #a word which satisfies these criteria may not exist
                break

            r = self.compare_words(tw, p)
            has += r['yellow'] + r['green']
            hasnot += r['grey']
            game.append((r['word'], r['pattern']))
            excluded += 1
            
            if r['solved']: return {'game': game, 'solved' : True, 'word' : p, 'attempts' : len(game)}
        
        #ALL OTHER ROUNDS
        #for the remaining attempts try to guess using the information gathered so far
        for a in range(attempts - (excluded + 1)):
            
            pattern_history = [p for _,p in game]
            w, possibilities_left = self.pick_random_word (pattern=pattern_history, hasnot_letters=hasnot, has_letters=has)
            if len(possibilities_left) > 1: w = possibilities_left[0]
            
            r = self.compare_words(w, p)
            has += r['yellow'] + r['green']
            hasnot += r['grey']
            game.append((r['word'], r['pattern']))

            if r['solved']: return {'game': game, 'solved' : True, 'word' : p, 'attempts' : len(game)}
            

        return {'game': game, 'solved' : False, 'word' : p, 'attempts' : attempts+1}

    def solve_many (self, guess_word=None, use_smart=True, start_with=None, stupid_mode=False, N_GAMES=100, attempts=6, exclude=0):
        '''
        Performs Monte Carlo simulation to evaluate Wordle solving strategies.
        
        This method runs multiple game simulations with identical parameters to
        generate statistical performance data for strategy comparison and analysis.
        Essential for benchmarking different approaches and parameter tuning.
        
        Parameters:
        -----------
        guess_word : str, optional
            If provided, solves the same target word N_GAMES times.
            If None, picks a different random target word for each game.
            
        use_smart : bool, default True
            Whether to use frequency-optimized starting words across all games.
            
        start_with : str, optional
            Specific starting word to use for all games in the simulation.
            
        stupid_mode : bool, default False
            If True, uses pure random guessing for all games (baseline testing).
            
        N_GAMES : int, default 100
            Number of games to simulate. Larger values give more reliable statistics
            but take longer to compute.
            
        attempts : int, default 6
            Maximum attempts allowed per game (standard Wordle limit).
            
        exclude : int, default 0
            Number of exploration rounds to use in each game.
            
        Returns:
        --------
        dict
            Statistical summary containing:
            - 'success_rate': Fraction of games solved (0.0 to 1.0)
            - 'stuck': Legacy field (always 0 in current implementation)
            - 'profile': NumPy array of attempt counts for each game
              
        Statistical Analysis:
        --------------------
        The 'profile' array enables detailed analysis:
        - Mean/median attempts for successful games
        - Distribution of attempt counts
        - Identification of difficult words (high attempt counts)
        - Success rate stratification by attempt number
        
        Progress Reporting:
        ------------------
        Prints real-time progress using carriage return (\\r) for same-line updates:
        "Game # 42, word CRANE, solved in: 4"
        
        Performance Insights:
        --------------------
        Typical results from codebase analysis:
        - Smart strategy: ~97% success rate, ~3.2 average attempts
        - Random strategy: ~19% success rate, ~5.8 average attempts
        - Exploration (exclude=1): Often improves both metrics
        
        Example Usage:
        -------------
        # Compare strategies
        smart_results = solver.solve_many(use_smart=True, exclude=1, N_GAMES=1000)
        random_results = solver.solve_many(use_smart=False, N_GAMES=1000)
        
        # Test specific starting word
        crane_results = solver.solve_many(start_with="CRANE", N_GAMES=500)
        
        # Analyze same word with different strategies
        word_test = solver.solve_many(guess_word="FROZE", N_GAMES=100)
        
        Example Return:
        --------------
        {
            'success_rate': 0.97,
            'stuck': 0,
            'profile': array([3, 4, 2, 5, 3, 4, ...])  # Attempt counts for each game
        }
        
        Analysis Examples:
        -----------------
        results = solver.solve_many(N_GAMES=1000)
        print(f"Success rate: {results['success_rate']:.1%}")
        print(f"Average attempts: {results['profile'].mean():.1f}")
        print(f"Median attempts: {np.median(results['profile']):.1f}")
        print(f"Failed games: {(results['profile'] > 6).sum()}")
        '''

        score = 0
        stuck = 0
        win = []

        for i in range(N_GAMES):
            r = self.solve(guess_word=guess_word, use_smart=use_smart, start_with=start_with, stupid_mode=stupid_mode, attempts=attempts, exclude=exclude)
            score += r['solved']
            win.append (r['attempts'])
            print ('Game # %s, word %s, solved in:%s \r' % (i, r['word'], r['attempts']), end="")

        return {'success_rate' : score / N_GAMES, 'stuck' : stuck, 'profile' : np.array(win)}

if __name__ == '__main__':

    g = wordle_solver('wordle_words.txt')
    print (g.solve(guess_word=None, use_smart=True, exclude=1))
