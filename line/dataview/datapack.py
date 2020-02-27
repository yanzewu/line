

class DataPack:

    def __init__(self, source=None):
        self.source = source

    def update(self, *args):
        pass
    


class StaticDataPack(DataPack):

    def __init__(self, data):
        self.data = data

    def update(self, newdata):
        self.data = newdata



class StaticPairedDataPack(DataPack):

    def __init__(self, x, y):
        assert x.shape == y.shape
        self.data = [x, y]

    def get_x(self):
        return self.data[0]

    def get_y(self):
        return self.data[1]

    def update(self, new_x=None, new_y=None):

        if new_x and new_y:
            assert new_x.shape == new_y.shape
            self.data = [new_x, new_y]
        elif new_x:
            assert new_x.shape == self.data[0].shape
            self.data[0] = new_x
        elif new_y:
            assert new_y.shape == self.data[1].shape
            self.data[1] = new_y


class DistributionDataPack(DataPack):

    def __init__(self, x, bins=10, norm='density'):
        self.data = x
        self.bins = bins
        self.norm = norm
        self._refresh()
        
    def _refresh(self):
        from ..sheet_util import histogram
        self._cache = histogram(self.data, self.bins, self.norm)

    def set_bins(self, bins):
        if bins != self.bins:
            self.bins = bins
            self._refresh()

    def set_norm(self, norm):
        if norm != self.norm:
            self.norm = norm
            self._refresh()

    def get_x(self):
        return self._cache[:, 0]

    def get_y(self):
        return self._cache[:, 1]

    def update(self, newdata):
        self.data = newdata
        self._refresh()
