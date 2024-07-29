import random
import string
class Sequence:
    def __init__(self, use_low=True, use_up=True, use_dig=True, use_spec=False, use_hex=False, use_hexlow=False, lows='',ups='',digs='',specs=''):
        try:
            self.eset = ''
            if not use_hex and not use_hexlow:
                if use_low:
                    self.eset += lows if type(lows)==str and lows.isalpha() and lows.islower() else string.ascii_lowercase
                if use_up:
                    self.eset += ups if type(ups)==str and ups.isalpha() and ups.isupper() else string.ascii_uppercase
                if use_spec:
                    self.eset += specs if type(specs)==str and 0<len(specs) and not specs.isalpha() and not specs.isnumeric() else string.punctuation
            else:
                self.eset += 'abcdef' if use_hexlow else 'ABCDEF'
            if use_dig:
                self.eset += digs if use_dig and type(digs)==str and digs.isnumeric() else string.digits
        except Exception as e:
            print(e)
            return ''

    def generate_sequence(self,size):
        if type(size)==int and 0<size<=1024:
            return ''.join(random.choice(self.eset) for _ in range(size))
        elif type(size)!=int:
            raise ValueError("Sequence size must be a Integer Class Object")
        else:
            raise ValueError("Sequence size must be Positive and less than 1024")

def generate_pattern(pattern,symbols_limit=''):
    try:
        if type(pattern)==str and 0<len(pattern)<=1024: 
            Sequence_set = {}
            if 'L' in pattern:
                Sequence_set['L'] = Sequence(use_low=True,use_up=False,use_dig=False)
            if 'U' in pattern:
                Sequence_set['U'] = Sequence(use_low=False,use_up=True,use_dig=False)
            if 'D' in pattern:
                Sequence_set['D'] = Sequence(use_low=False,use_up=False,use_dig=True)
            if 'S' in pattern:
                Sequence_set['S'] = Sequence(use_low=False,use_up=False,use_dig=False,use_spec=True, specs=symbols_limit)
            if 'H' in pattern:
                Sequence_set['H'] = Sequence(use_low=False,use_up=False,use_dig=True,use_hex=True)
            if 'h' in pattern:
                Sequence_set['h'] = Sequence(use_low=False,use_up=False,use_dig=True,use_hexlow=True)
            if 'F' in pattern:
                Sequence_set['F'] = Sequence(use_low=False,use_up=False,use_dig=False,use_hex=True)
            if 'f' in pattern:
                Sequence_set['f'] = Sequence(use_low=False,use_up=False,use_dig=False,use_hexlow=True)
            if Sequence_set:
                return ''.join([Sequence_set[p].generate_sequence(size=1) for p in pattern if p in 'LUDSHhFf'])
            else:
                raise ValueError("Pattern does not contain any valid declarations")
        elif type(pattern)!=str:
            raise ValueError("Pattern must be a String Class Object")
        else:
            raise ValueError("Pettern must not be empty and it's size should be less than 1024 characters")
    except Exception as e:
        print(e)
        return ''

if __name__=="__main__":
    print(generate_pattern("ULULDDSHhFf",symbols_limit="@"))