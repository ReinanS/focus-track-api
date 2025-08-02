class AttentionScorer:
    """
    Attention Scorer class that contains methods for estimating EAR, Gaze_Score, PERCLOS and Head Pose over time,
    with the given thresholds (time thresholds and value thresholds)

    Methods
    ----------
    - eval_scores: used to evaluate the driver's state of attention
    - get_PERCLOS: specifically used to evaluate the driver sleepiness
    """

    def __init__(
        self,
        t_now,
    ):
        """
        Initialize the AttentionScorer object with the given thresholds and parameters.

        Parameters
        ----------
        t_now: float or int
            The current time in seconds.

        ear_thresh: float or int
            EAR score value threshold (if the EAR score is less than this value, eyes are considered closed!)

        gaze_thresh: float or int
            Gaze Score value threshold (if the Gaze Score is more than this value, the gaze is considered not centered)

        perclos_thresh: float (ranges from 0 to 1), optional
            PERCLOS threshold that indicates the maximum time allowed in 60 seconds of eye closure
            (default is 0.2 -> 20% of 1 minute)

        roll_thresh: int, optional
            The roll angle increases or decreases when you turn your head clockwise or counter clockwise.
            Threshold of the roll angle for considering the person distracted/unconscious (not straight neck)
            Default threshold is 20 degrees from the center position.

        pitch_thresh: int, optional
            The pitch angle increases or decreases when you move your head upwards or downwards.
            Threshold of the pitch angle for considering the person distracted (not looking in front)
            Default threshold is 20 degrees from the center position.

        yaw_thresh: int, optional
            The yaw angle increases or decreases when you turn your head to left or right.
            Threshold of the yaw angle for considering the person distracted/unconscious (not straight neck)
            It increase or decrease when you turn your head to left or right. default is 20 degrees from the center position.

        ear_time_thresh: float or int, optional
            Maximum time allowable for consecutive eye closure (given the EAR threshold considered)
            (default is 4.0 seconds)

        gaze_time_thresh: float or int, optional
            Maximum time allowable for consecutive gaze not centered (given the Gaze Score threshold considered)
            (default is 2.0 seconds)

        pose_time_thresh: float or int, optional
            Maximum time allowable for consecutive distracted head pose (given the pitch,yaw and roll thresholds)
            (default is 4.0 seconds)

        verbose: bool, optional
            If set to True, print additional information about the scores (default is False)
        """

        # constant for the PERCLOS time period
        self.PERCLOS_TIME_PERIOD = 60

        # setting for the attention scorer thresholds
        self.ear_thresh = 0.15
        self.gaze_thresh = 0.015
        self.perclos_thresh = 0.2
        self.roll_thresh = 60
        self.pitch_thresh = 20
        self.yaw_thresh = 30
        self.ear_time_thresh = 12.0
        self.gaze_time_thresh = 6.0
        self.pose_time_thresh = 12.0

        # previous timestamp variable and counter/timer variables
        self.last_time_eye_opened = t_now
        self.last_time_looked_ahead = t_now
        self.last_time_attended = t_now
        self.prev_time = t_now

        self.closure_time = 0
        self.not_look_ahead_time = 0
        self.distracted_time = 0
        self.eye_closure_counter = 0
        self.total_closed_frames = 0
        self.total_frames = 0

        # Para PERCLOS com janela deslizante
        self.eye_closure_history = []  # Lista de timestamps de frames com olhos fechados
        self.frame_history = []  # Lista de timestamps de todos os frames

        # verbose flag
        self.verbose = False

    def eval_scores(
        self, t_now, ear_score, gaze_score, head_roll, head_pitch, head_yaw
    ):
        # converte para float para evitar arrays
        roll = float(head_roll)
        pitch = float(head_pitch)
        yaw = float(head_yaw)
        """
        Evaluate the driver's state of attention based on the given scores and thresholds.

        Returns
        -------
        asleep: bool
            Indicates if the driver is asleep or not.
        looking_away: bool
            Indicates if the driver is looking away or not.
        distracted: bool
            Indicates if the driver is distracted or not.
        """

        # Sub-funções internas para clareza
        def is_eye_closed(score):
            return score is not None and score <= self.ear_thresh

        def is_looking_away(score):
            return score is not None and score > self.gaze_thresh

        def is_pose_distracted(roll, pitch, yaw):
            return any([
                roll is not None and abs(roll) > self.roll_thresh,
                pitch is not None and abs(pitch) > self.pitch_thresh,
                yaw is not None and abs(yaw) > self.yaw_thresh,
            ])

        def is_pose_attentive(roll, pitch, yaw):
            if None in {roll, pitch, yaw}:
                return True
            return all([
                abs(roll) <= self.roll_thresh,
                abs(pitch) <= self.pitch_thresh,
                abs(yaw) <= self.yaw_thresh,
            ])

        # Atualiza timers e contadores
        if is_eye_closed(ear_score):
            self.closure_time = t_now - self.last_time_eye_opened
        else:
            self.last_time_eye_opened = t_now
            self.closure_time = 0.0

        if is_looking_away(gaze_score):
            self.not_look_ahead_time = t_now - self.last_time_looked_ahead
        else:
            self.last_time_looked_ahead = t_now
            self.not_look_ahead_time = 0.0

        if is_pose_distracted(roll, pitch, yaw):
            self.distracted_time = t_now - self.last_time_attended
        elif is_pose_attentive(roll, pitch, yaw):
            self.last_time_attended = t_now
            self.distracted_time = 0.0

        # Avalia o estado com base nos thresholds
        asleep = self.closure_time >= self.ear_time_thresh
        looking_away = self.not_look_ahead_time >= self.gaze_time_thresh
        distracted = self.distracted_time >= self.pose_time_thresh

        return asleep, looking_away, distracted

    def get_PERCLOS(self, t_now, fps, ear_score):
        """
        Compute the PERCLOS (Percentage of Eye Closure) score over a given time period.

        Parameters
        ----------
        t_now: float or int
            The current time in seconds.

        fps: int
            The frames per second of the video.

        ear_score: float
            EAR (Eye Aspect Ratio) score obtained from the driver eye aperture.

        Returns
        -------
        tired: bool
            Indicates if the driver is tired or not.

        perclos_score: float
            The PERCLOS score over a minute.
        """

        tired = False  # set default value for the tired state of the driver

        # Adicionar timestamp atual ao histórico de frames
        self.frame_history.append(t_now)

        # Se olhos estão fechados, adicionar ao histórico
        if (ear_score is not None) and (ear_score <= self.ear_thresh):
            self.eye_closure_history.append(t_now)

        # Limpar histórico antigo (mais de 60 segundos atrás)
        cutoff_time = t_now - self.PERCLOS_TIME_PERIOD
        self.frame_history = [
            t for t in self.frame_history if t >= cutoff_time
        ]
        self.eye_closure_history = [
            t for t in self.eye_closure_history if t >= cutoff_time
        ]

        # Calcular PERCLOS baseado na janela deslizante
        if len(self.frame_history) > 0:
            perclos_score = len(self.eye_closure_history) / len(
                self.frame_history
            )
        else:
            perclos_score = 0.0

        if perclos_score >= self.perclos_thresh:
            tired = True

        # Atualiza contadores acumulativos da sessão (para estatísticas finais)
        self.total_frames += 1
        if (ear_score is not None) and (ear_score <= self.ear_thresh):
            self.total_closed_frames += 1

        return tired, perclos_score
