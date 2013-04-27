class NoneType:
    pass


class ClassTags(object):
    def __init__(self, classes):
        self._class_to_tag = dict(zip(classes, range(len(classes))))
        self._tag_to_class = dict(zip(range(len(classes)), classes))

        if len(classes) > 255:
            raise Exception('Cannot have more than 255 polymorphic tags')


    def class_to_tag(self, cls):
        return self._class_to_tag[cls]

    def tag_to_class(self, tag):
        return self._tag_to_class[tag]
