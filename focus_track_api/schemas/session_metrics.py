class SessionMetrics:
    def __init__(self):
        self.attention_scores = []
        self.fatigue_scores = []
        self.distraction_scores = []
        self.distraction_threshold = 60

        self.frames_total = 0
        self.frames_distracted = 0
        self.max_fatigue = 0
        self.max_distraction = 0

    def update(self, fatigue, distraction, attention):
        self.attention_scores.append(attention)
        self.fatigue_scores.append(fatigue)
        self.distraction_scores.append(distraction)

        self.max_fatigue = max(self.max_fatigue, fatigue)
        self.max_distraction = max(self.max_distraction, distraction)

        self.frames_total += 1
        if distraction > self.distraction_threshold:
            self.frames_distracted += 1

    def summary(self):
        avg_attention = (
            sum(self.attention_scores) / len(self.attention_scores)
            if self.attention_scores
            else 0.0
        )
        avg_fatigue = (
            sum(self.fatigue_scores) / len(self.fatigue_scores)
            if self.fatigue_scores
            else 0.0
        )
        avg_distraction = (
            sum(self.distraction_scores) / len(self.distraction_scores)
            if self.distraction_scores
            else 0.0
        )
        distraction_rate = (
            (self.frames_distracted / self.frames_total) * 100
            if self.frames_total > 0
            else 0.0
        )

        return {
            'average_attention_score': avg_attention,
            'average_fatigue': avg_fatigue,
            'average_distraction': avg_distraction,
            'distraction_rate': distraction_rate,
            'max_fatigue': self.max_fatigue,
            'max_distraction': self.max_distraction,
        }
