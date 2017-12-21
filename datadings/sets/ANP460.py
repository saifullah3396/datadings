from ..reader import MsgpackReader as ANP460Reader


class ANP460Data(dict):
    def __init__(self, image, experiments, key, anp, type):
        super(ANP460Data, self).__init__(
            image=image, experiments=experiments, key=key,
            anp=anp, type=type,
        )


class ANP460Experiment(dict):
    def __init__(self, locations, map, answer, duration):
        super(ANP460Experiment, self).__init__(
            locations=locations, map=map, answer=answer, duration=duration,
        )
