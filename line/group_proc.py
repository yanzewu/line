

class GroupDesc:

    REPEAT_COLOR = 1
    REPEAT_GROUP = 2

    def __init__(self, repeat_style=REPEAT_COLOR, prefix=None, repeator=None, suffix=None):
        """ Describe a group.
        repeat_style: REPEAT_COLOR (repeat color_id) or REPEAT_GROUP (repeat group_id). If REPEAT_GROUP,
            the member in repeator must have same color_id.
        prefix, repeator, suffix: List of color_id (int) starting from 1. color_id = 0 has special meaning:
            it marks the 'base' group.
        """
        self.repeat_style = repeat_style
        self.prefix = prefix if prefix is not None else []
        self.repeator = repeator if repeator is not None else []
        self.suffix = suffix if suffix is not None else []

    def __str__(self):
        return '%s group: %s-%s-%s' % (
            'normal' if self.repeat_style == GroupDesc.REPEAT_COLOR else 'inc',
            self.prefix,
            self.repeator,
            self.suffix)

    def generate_ids(self, length):
        """ Generate the group_ids and color_ids required 
        """

        cidx_refnum = [1] * (max(self.prefix+self.repeator+self.suffix)+1)   # occurrence of colorid
        colorids = []
        groupids = []

        for idx, cidx in enumerate(self.prefix):
            colorids.append(cidx)
            if cidx != 0:
                groupids.append(cidx_refnum[cidx])
                cidx_refnum[cidx] += 1
            else:
                groupids.append(0)

        if self.repeator and length > len(self.prefix) + len(self.suffix):
            if self.repeat_style == GroupDesc.REPEAT_COLOR:
                for idx in range(len(self.prefix), length-len(self.suffix)):
                    cidx = self.repeator[(idx - len(self.prefix))%len(self.repeator)]
                    colorids.append(cidx)
                    if cidx != 0:
                        groupids.append(cidx_refnum[cidx])
                        cidx_refnum[cidx] += 1
                    else:
                        groupids.append(0)
            elif self.repeat_style == GroupDesc.REPEAT_GROUP:
                cidx = colorids[-1]
                for idx in range(len(self.prefix), length-len(self.suffix)):
                    groupids.append((idx - len(self.prefix))%len(self.repeator) + 1)
                    colorids.append(cidx + (idx - len(self.prefix))//len(self.repeator) + 1)
            else:
                raise ValueError(self.repeat_style)

        if self.suffix:
            for idx in range(max(len(self.prefix), length-len(self.suffix)), length):
                cidx = self.suffix[idx - length + len(self.suffix)]
                colorids.append(cidx)
                if cidx != 0:
                    groupids.append(cidx_refnum[cidx])
                    cidx_refnum[cidx] += 1
                else:
                    groupids.append(0)

        return colorids, groupids


def parse_group(group:str):
    """ str -> GroupDesc
    """

    order = _text_order(group.replace('...', ''))

    if '...' in group:
        prefix, suffix = group.split('...')
        i = len(prefix)-1
        repeator = prefix[i]
        while i > len(prefix)//2:
            if prefix[2*i - len(prefix):i] == prefix[i:]:
                repeator = prefix[i:]
            i -= 1

        repeat_style = GroupDesc.REPEAT_COLOR
        if len(repeator) == 1:
            i = len(prefix)-1
            r1 = 0
            r2 = 0
            while i > 0:
                if prefix[i-1] == prefix[i]:
                    pass
                elif r1 == 0:
                    r1 = len(prefix) - i
                elif r2 == 0:
                    r2 = len(prefix) - i - r1
                    break
                i -= 1
            if r1 == r2 and r1 > 1:
                repeat_style = GroupDesc.REPEAT_GROUP
                repeator = prefix[len(prefix)-r1:]
            print(r1, r2)

        if repeat_style == GroupDesc.REPEAT_COLOR:
            prefix = prefix[:len(prefix)-len(repeator)]

        return GroupDesc(
            repeat_style,
            [order[t] for t in prefix], 
            [order[t] for t in repeator], 
            [order[t] for t in suffix]
            )

    else:
        return GroupDesc(GroupDesc.REPEAT_COLOR, [order[t] for t in group])


def _text_order(text):
    order = {'0':0}
    i = 1
    for t in text:
        if t not in order:
            order[t] = i
            i += 1
    return order
