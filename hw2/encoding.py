import struct

class Encoder:
    def __init__(self):
        pass
    
    """encode array of integers"""
    def encode(self, arr):
        pass
    
    """decode encoded array into array of integers"""
    def decode(self, encoded):
        pass


class Varbyte(Encoder):
    def __init__(self):
        Encoder.__init__(self)
    
    """encode array of integers into string"""
    def encode(self, arr):
        Encoded = ""
        for numb in arr:
            #last byte
            byte = (numb & 0b01111111) | 0b10000000
            packed_bytes = chr(byte)
            #other bytes
            while(numb & ~0b01111111 != 0):
                numb >>= 7
                byte = (numb & 0b01111111)
                packed_bytes = chr(byte) + packed_bytes
            Encoded += packed_bytes
        return Encoded

    def decode(self, encoded):
        Nums = []
        numb = 0
        for char in encoded:
            byte = ord(char)
            if(byte & 0b10000000 == 0):
                numb = (numb << 7) | byte
            else:
                numb = (numb << 7) | (byte & 0b01111111)
                Nums.append(numb)
                numb = 0
        return Nums


class Simple9(Encoder):
    """encode array of integers into string
    code 0: 28 of 1-bit numbs
    code 1: 14 of 2-bit numbs
    code 2: 9 of 3-bit numbs
    code 3: 7 of 4-bit numbs
    code 4: 5 of 5-bit numbs
    code 5: 4 of 7-bit numbs
    code 6: 3 of 9-bit numbs
    code 7: 2 of 14-bit numbs
    code 8: 1 of 28-bit numb
    """
    def __init__(self):
        Encoder.__init__(self)
        self.bitsize_lst = [1, 2, 3, 4, 5, 7, 9, 14, 28]
        self.count_lst = [28, 14, 9, 7, 5, 4, 3, 2, 1]
        self.mask_lst = [0x8000000, 0xc000000, 0xe000000, 
                         0xf000000, 0xf800000, 0xfe00000, 
                         0xff80000, 0xfffc000, 0xfffffff]
    
    def _pack_word(self, code, numbs):
        word = code
        for numb in numbs:
            word <<= self.bitsize_lst[code]
            word |= numb
        """add extra bits to fill the word"""
        if(code == 2 or code == 6):
            word <<= 1
        if(code == 4):
            word <<= 3
        return struct.pack('I', word)
        
    def encode(self, arr):
        Encoded = ""
        code = 8
        cur_pack = []
        i = 0
        while(i < len(arr)):
            is_last = (i == len(arr) - 1)
            numb = arr[i]
            cur_pack.append(numb)
            prev_code = code + 1
            if(max(cur_pack) < 2**self.bitsize_lst[code]):
                if(len(cur_pack) < self.count_lst[code]):
                    if(is_last):
                        """pack previous suited state of cur_pack"""
                        Encoded += self._pack_word(prev_code, cur_pack[:self.count_lst[prev_code]])
                        """handle tail: just get back on tail size and start new iteration with resetted state"""
                        i -= len(cur_pack[self.count_lst[prev_code] :])
                        """reset state"""
                        code = 8
                        cur_pack = []
                    else:
                        """able to add more numbers with this bitsize"""
                        pass
                else:
                    if((code == 0) or is_last):
                        """final situation reached; time to pack"""
                        Encoded += self._pack_word(code, cur_pack)
                        code = 8
                        cur_pack = []
                    else:
                        """trying to make smaller"""
                        code -= 1
            else:
                """pack previous suited state of cur_pack"""
                Encoded += self._pack_word(prev_code, cur_pack[:self.count_lst[prev_code]])
                """handle tail: just get back on tail size and start new iteration with resetted state"""
                i -= len(cur_pack[self.count_lst[prev_code] :])
                """reset state"""
                code = 8
                cur_pack = []
            i += 1
        return Encoded
            
    def decode(self, encoded):
        Nums = []
        for i in xrange(len(encoded)/4):
            word = struct.unpack('I', encoded[4 * i : 4 * (i + 1)])[0]
            code = word >> 28
            payload = word & 0x0fffffff
            for n in xrange(self.count_lst[code]):
                numb = (payload & self.mask_lst[code]) >> (28 - self.bitsize_lst[code])
                Nums.append(numb)
                payload <<= self.bitsize_lst[code]
        return Nums
