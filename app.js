/**
 * Friendship Meter - Soft, casual, English-Marathi friendship quiz
 * 8-question quiz, initial score, distance challenge, final 80/20 score,
 * combined vacation postcard + location challenge with consented GPS transmission.
 */

(function () {
  'use strict';

  // --- Sound Effects Engine (Gentle Web Audio API) ---
  let soundEnabled = true;
  let audioCtx = null;

  function initAudio() {
    if (!audioCtx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) {
        audioCtx = new AudioContext();
      }
    }
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
  }

  function playTone(freq, duration = 0.1, type = 'sine', gainVal = 0.08) {
    if (!soundEnabled) return;
    try {
      initAudio();
      if (!audioCtx) return;
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
      gain.gain.setValueAtTime(gainVal, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + duration);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + duration);
    } catch (e) {}
  }

  function playPop() {
    playTone(440, 0.08, 'sine', 0.06);
    setTimeout(() => playTone(880, 0.08, 'sine', 0.06), 40);
  }

  function playChime() {
    playTone(523.25, 0.12, 'sine', 0.08); // C5
    setTimeout(() => playTone(659.25, 0.14, 'sine', 0.08), 80); // E5
    setTimeout(() => playTone(783.99, 0.2, 'sine', 0.09), 160); // G5
  }

  function playVictoryFanfare() {
    const notes = [523.25, 659.25, 783.99, 1046.50];
    notes.forEach((f, i) => {
      setTimeout(() => playTone(f, 0.16, 'sine', 0.1), i * 110);
    });
  }

  function triggerHaptic() {
    if (navigator.vibrate) {
      try { navigator.vibrate(12); } catch (e) {}
    }
  }

  // --- Eight Friendship Meter Questions ---
  const QUIZ_QUESTIONS = [
    {
      question: "What's your ideal plan?",
      subtitle: "a regular weekend vibe check",
      options: [
        { text: "Chai ani gappa", score: 12.5, reaction: "classic! ek cutting chai & unlimited talks." },
        { text: "Long drive, random songs", score: 12.5, reaction: "playlist sorted, vibe set!" },
        { text: "Gharich basu, please", score: 10.0, reaction: "introvert peace mode activated." },
        { text: "Plan karu, cancel karu", score: 7.5, reaction: "chaotic relatable energy haha!" }
      ]
    },
    {
      question: "Someone says \"kahi nahi\" — what does it mean?",
      subtitle: "decoding the iconic marathi expression",
      options: [
        { text: "Bharpur kahi tari aahe", score: 12.5, reaction: "100% correct! emotional intelligence peak." },
        { text: "Mood off aahe, clearly", score: 11.0, reaction: "spot on, something is definitely brewing." },
        { text: "Depends on the person", score: 9.0, reaction: "analytical mind, safe answer." },
        { text: "Literally kahi nahi", score: 6.0, reaction: "naive or super optimistic!" }
      ]
    },
    {
      question: "A 10-minute call becomes 2 hours. Why?",
      subtitle: "late-night phone call lore",
      options: [
        { text: "Gossip cha stock sampat nahi", score: 12.5, reaction: "the tea was too hot to hang up!" },
        { text: "Arey, time kasa gela kalalach nahi", score: 12.5, reaction: "true connection sign right here." },
        { text: "Ek topic varun dusra", score: 10.0, reaction: "rabbit hole jumping champions." },
        { text: "Comfortable silence pan chalta", score: 11.0, reaction: "that's rare and top tier." }
      ]
    },
    {
      question: "Best way to fix a bad mood?",
      subtitle: "emergency dopamine protocol",
      options: [
        { text: "Chaha ani kahi tari khaayla", score: 12.5, reaction: "food + chai = 99% problems solved." },
        { text: "Ek mast rant session", score: 12.5, reaction: "venting without filter is medicinal." },
        { text: "Memes pathav, lecture nako", score: 11.0, reaction: "zero gyaan, pure brainrot memes." },
        { text: "Thoda time ani peace", score: 10.0, reaction: "recharging the social battery." }
      ]
    },
    {
      question: "\"Kay challay?\" usually means…",
      subtitle: "universal marathi greeting probe",
      options: [
        { text: "Kahi gossip aahe ka?", score: 12.5, reaction: "always on detective mode!" },
        { text: "Bore zhaloy, bol na", score: 12.0, reaction: "call for emergency entertainment." },
        { text: "Genuine update pahije", score: 10.0, reaction: "wholesome check-in." },
        { text: "Just checking in", score: 8.0, reaction: "polite and gentle." }
      ]
    },
    {
      question: "What's your texting personality?",
      subtitle: "the notification response style",
      options: [
        { text: "Instant reply gang", score: 12.5, reaction: "online speedrunner status!" },
        { text: "Voice notes supremacy", score: 12.0, reaction: "mini podcast creator detected." },
        { text: "Depends on my mood yaar", score: 10.0, reaction: "unpredictable like monsoon." },
        { text: "Reply in my head, forget IRL", score: 7.5, reaction: "the classic ghosting by mistake!" }
      ]
    },
    {
      question: "Last-minute plan: \"Chal, baher jau.\"",
      subtitle: "spontaneous invite reaction",
      options: [
        { text: "Location pathav, I'm ready", score: 12.5, reaction: "gold standard friend behavior!" },
        { text: "Kuthay? Kiti vajta? Kon yenar?", score: 11.0, reaction: "operations manager of the group." },
        { text: "Aai la vicharun sangto", score: 9.0, reaction: "sanskaari priority check." },
        { text: "Udyala jau, aaj blanket day", score: 7.5, reaction: "blanket cocoon cannot be broken." }
      ]
    },
    {
      question: "When someone teases you, you…",
      subtitle: "banter dynamics",
      options: [
        { text: "Teasing back is my love language", score: 12.5, reaction: "mutual roast session is true friendship!" },
        { text: "Full comeback ready aahe", score: 12.5, reaction: "armed with quick wit!" },
        { text: "Laugh karto, mag revenge", score: 11.0, reaction: "playing the long game, dangerous." },
        { text: "Pretend ki farak padat nahi", score: 8.0, reaction: "stone-faced poker master." }
      ]
    }
  ];

  // --- Vacation Recommendations Curated Data ---
  const VACATIONS = [
    {
      title: "Lonavala & Khandala",
      icon: "⛰️",
      tagline: "Chai, foggy hills & chikki stops",
      desc: "Perfect hill-station escape for endless gappa, hot onion pakodas, and scenic viewpoints without rushing anywhere.",
      why: "Your answers showed love for cozy vibes, chai sessions, and comfortable banter over hectic tourism."
    },
    {
      title: "Alibaug & Kashid Beach",
      icon: "🏖️",
      tagline: "Sea breeze, tender coconut & sunset walks",
      desc: "Hop on a ferry or road trip down the coastal road. Sand, chilled water, fresh seafood, and evening music.",
      why: "You love spontaneous plans and music-filled drives where time flows without anyone watching the clock."
    },
    {
      title: "FC Road & Koregaon Park, Pune",
      icon: "☕",
      tagline: "Café-hopping, cold coffee & street food",
      desc: "A relaxed day hopping from iconic bun maska spots to aesthetic specialty coffee corners and endless conversations.",
      why: "You're all about high-speed gossip, instant banter, and good snacks keeping the energy alive."
    },
    {
      title: "Tamhini Ghat Road Trip",
      icon: "🚗",
      tagline: "Misty curves, waterfalls & playlist magic",
      desc: "Winding roads, lush green hills, cutting chai at roadside shacks, and shouting lyrics to your favorite songs.",
      why: "Your spontaneous 'Chal baher jau' mindset makes you the ideal road trip copilot."
    }
  ];

  // --- Game State ---
  const state = {
    sessionId: 'fm_' + Math.random().toString(36).substring(2, 10),
    screen: 'welcome',
    playerAlias: '',
    currentQuizIndex: 0,
    answers: [], // stores { qIdx, qText, optText, scoreVal }
    quizScore: 0,
    initialBand: '',
    distanceKm: null,
    distanceDisplay: '',
    distanceScore: null,
    distanceCaption: '',
    finalScore: null,
    finalBand: '',
    locationPermission: null,
    locationData: null, // { latitude, longitude, accuracy, timestamp }
    hasLocationConsent: false
  };

  // --- DOM Elements ---
  const screens = {
    welcome: document.getElementById('screen-welcome'),
    quiz: document.getElementById('screen-quiz'),
    initialScore: document.getElementById('screen-initial-score'),
    distanceChallenge: document.getElementById('screen-distance-challenge'),
    finalScore: document.getElementById('screen-final-score'),
    vacationChallenge: document.getElementById('screen-vacation-challenge')
  };

  const headerBackBtn = document.getElementById('header-back-btn');
  const stepBadgeText = document.getElementById('step-badge-text');
  const soundToggleBtn = document.getElementById('sound-toggle');
  const soundIcon = document.getElementById('sound-icon');

  // Quiz progress bar
  const quizProgressWrap = document.getElementById('quiz-progress-wrap');
  const quizStepLabel = document.getElementById('quiz-step-label');
  const quizPercentLabel = document.getElementById('quiz-percent-label');
  const quizProgressFill = document.getElementById('quiz-progress-fill');

  // Screen 1: Welcome
  const playerAliasInput = document.getElementById('player-alias-input');
  const btnStartQuiz = document.getElementById('btn-start-quiz');

  // Screen 2: Quiz
  const quizQuestionTag = document.getElementById('quiz-question-tag');
  const quizQuestionTitle = document.getElementById('quiz-question-title');
  const quizQuestionSub = document.getElementById('quiz-question-sub');
  const quizOptionsContainer = document.getElementById('quiz-options-container');
  const quizReactionBubble = document.getElementById('quiz-reaction');
  const quizReactionText = document.getElementById('quiz-reaction-text');
  const btnPrevQuestion = document.getElementById('btn-prev-question');
  const quizHintText = document.getElementById('quiz-hint-text');

  // Screen 3: Initial Score
  const initialScoreNum = document.getElementById('initial-score-num');
  const initialScoreBar = document.getElementById('initial-score-bar');
  const initialScoreBand = document.getElementById('initial-score-band');
  const initialScoreDesc = document.getElementById('initial-score-desc');
  const btnToDistanceChallenge = document.getElementById('btn-to-distance-challenge');

  // Screen 4: Distance Challenge
  const btnCalcDistance = document.getElementById('btn-calc-distance');
  const btnBackToScore = document.getElementById('btn-back-to-score');
  const distanceStatusBox = document.getElementById('distance-status-box');
  const distanceSpinner = document.getElementById('distance-spinner');
  const distanceStatusText = document.getElementById('distance-status-text');
  const btnDistanceRetry = document.getElementById('btn-distance-retry');
  const distanceResultCard = document.getElementById('distance-result-card');
  const distanceValText = document.getElementById('distance-val-text');
  const distanceCaptionText = document.getElementById('distance-caption-text');
  const distanceContinueBar = document.getElementById('distance-continue-bar');
  const btnToFinalScore = document.getElementById('btn-to-final-score');

  // Screen 5: Final Score
  const finalScoreNum = document.getElementById('final-score-num');
  const finalScoreBar = document.getElementById('final-score-bar');
  const finalScoreBand = document.getElementById('final-score-band');
  const finalScoreDesc = document.getElementById('final-score-desc');
  const breakdownQuizVal = document.getElementById('breakdown-quiz-val');
  const breakdownQuizContrib = document.getElementById('breakdown-quiz-contrib');
  const breakdownDistVal = document.getElementById('breakdown-dist-val');
  const breakdownDistContrib = document.getElementById('breakdown-dist-contrib');
  const btnToVacationChallenge = document.getElementById('btn-to-vacation-challenge');

  // Screen 6: Combined Vacation + Location Challenge
  const postcardIcon = document.getElementById('postcard-icon');
  const postcardTitle = document.getElementById('postcard-title');
  const postcardTagline = document.getElementById('postcard-tagline');
  const postcardDesc = document.getElementById('postcard-desc');
  const postcardWhyText = document.getElementById('postcard-why-text');
  const consentAgreementChk = document.getElementById('consent-agreement-chk');
  const btnGoForIt = document.getElementById('btn-go-for-it');
  const challengeStatusBox = document.getElementById('challenge-status-box');
  const challengeSpinner = document.getElementById('challenge-spinner');
  const challengeStatusText = document.getElementById('challenge-status-text');
  const btnChallengeRetry = document.getElementById('btn-challenge-retry');
  const revealSuccessBox = document.getElementById('reveal-success-box');
  const coordsText = document.getElementById('coords-text');
  const coordsAccuracy = document.getElementById('coords-accuracy');
  const mapLinkBtn = document.getElementById('map-link-btn');
  const btnCopySummary = document.getElementById('btn-copy-summary');
  const btnPlayAgain = document.getElementById('btn-play-again');
  const confettiCanvas = document.getElementById('confetti-canvas');

  // --- Result Band Helper ---
  function getResultBand(score) {
    score = Math.round(score);
    if (score < 40) return "Ajun olakh vhaychi aahe";
    if (score < 60) return "Chai-pani acquaintances";
    if (score < 80) return "Gappa gang material";
    if (score < 95) return "Gappa Champion";
    return "Full-time bakbak partner";
  }

  function getBandDescription(band) {
    switch (band) {
      case "Full-time bakbak partner":
        return "Peak compatibility! 2-hour phone calls, unspoken Marathi humor, and effortless gappa mode.";
      case "Gappa Champion":
        return "Solid frequency match! Ready for chai breaks, endless banter, and zero awkward pauses.";
      case "Gappa gang material":
        return "Mast potential aahe! Good humor, relatable habits, and always up for some fun teasing.";
      case "Chai-pani acquaintances":
        return "Thoda formal aahe ajun, but a couple of cutting chais and good memes will break the ice!";
      default:
        return "Ajun olakh vhaychi aahe! Need more conversations and shared playlists to unlock the full vibe.";
    }
  }

  // --- Navigation & Header Control ---
  function showScreen(name) {
    state.screen = name;
    Object.keys(screens).forEach(k => {
      screens[k].classList.remove('active');
    });

    if (screens[name]) {
      screens[name].classList.add('active');
      screens[name].scrollTop = 0;
    }

    // Header Back button control
    if (name === 'quiz' && state.currentQuizIndex > 0) {
      headerBackBtn.style.visibility = 'visible';
    } else if (name === 'distanceChallenge') {
      headerBackBtn.style.visibility = 'visible';
    } else {
      headerBackBtn.style.visibility = 'hidden';
    }

    // Step Badge and Progress Bar
    switch (name) {
      case 'welcome':
        stepBadgeText.textContent = 'Friendship Meter';
        quizProgressWrap.style.display = 'none';
        break;
      case 'quiz':
        stepBadgeText.textContent = `quiz • ${state.currentQuizIndex + 1}/8`;
        quizProgressWrap.style.display = 'block';
        updateQuizProgress();
        break;
      case 'initialScore':
        stepBadgeText.textContent = 'initial vibe score';
        quizProgressWrap.style.display = 'none';
        break;
      case 'distanceChallenge':
        stepBadgeText.textContent = 'distance challenge 📍';
        quizProgressWrap.style.display = 'none';
        break;
      case 'finalScore':
        stepBadgeText.textContent = 'final rating 80/20';
        quizProgressWrap.style.display = 'none';
        break;
      case 'vacationChallenge':
        stepBadgeText.textContent = 'getaway & challenge 🌍';
        quizProgressWrap.style.display = 'none';
        break;
    }
  }

  function updateQuizProgress() {
    const total = QUIZ_QUESTIONS.length;
    const current = state.currentQuizIndex + 1;
    const pct = Math.round((current / total) * 100);
    quizStepLabel.textContent = `Question ${current} of ${total}`;
    quizPercentLabel.textContent = `${pct}%`;
    quizProgressFill.style.width = `${pct}%`;
  }

  // Header back button
  headerBackBtn.addEventListener('click', () => {
    triggerHaptic();
    playPop();
    if (state.screen === 'quiz' && state.currentQuizIndex > 0) {
      state.currentQuizIndex--;
      renderQuizQuestion(state.currentQuizIndex);
    } else if (state.screen === 'distanceChallenge') {
      showScreen('initialScore');
    }
  });

  // Sound toggle
  soundToggleBtn.addEventListener('click', () => {
    initAudio();
    soundEnabled = !soundEnabled;
    soundIcon.textContent = soundEnabled ? '🔈' : '🔇';
    if (soundEnabled) playPop();
  });

  // --- Screen 1: Start Quiz ---
  btnStartQuiz.addEventListener('click', () => {
    initAudio();
    triggerHaptic();
    playChime();
    state.playerAlias = playerAliasInput.value.trim() || 'Friend';
    state.currentQuizIndex = 0;
    state.answers = [];
    renderQuizQuestion(0);
    showScreen('quiz');
  });

  // --- Screen 2: 8-Question Quiz Engine ---
  function renderQuizQuestion(index) {
    const q = QUIZ_QUESTIONS[index];
    quizQuestionTag.textContent = `question ${index + 1} of ${QUIZ_QUESTIONS.length}`;
    quizQuestionTitle.textContent = q.question;
    quizQuestionSub.textContent = q.subtitle;

    quizOptionsContainer.innerHTML = '';
    quizReactionBubble.classList.remove('visible');

    // Back nav button visibility inside screen
    btnPrevQuestion.style.display = index > 0 ? 'inline-block' : 'none';
    quizHintText.style.display = 'inline-block';

    const letters = ['A', 'B', 'C', 'D'];
    const currentAnswer = state.answers[index];

    q.options.forEach((opt, optIdx) => {
      const card = document.createElement('div');
      card.className = 'quiz-option-card';
      if (currentAnswer && currentAnswer.optText === opt.text) {
        card.classList.add('selected');
      }

      card.innerHTML = `
        <span class="opt-bullet">${letters[optIdx]}</span>
        <span class="opt-text">${opt.text}</span>
      `;

      card.addEventListener('click', () => {
        handleOptionSelect(index, q, opt, card);
      });

      quizOptionsContainer.appendChild(card);
    });

    updateQuizProgress();
    stepBadgeText.textContent = `quiz • ${index + 1}/8`;
  }

  btnPrevQuestion.addEventListener('click', () => {
    triggerHaptic();
    playPop();
    if (state.currentQuizIndex > 0) {
      state.currentQuizIndex--;
      renderQuizQuestion(state.currentQuizIndex);
    }
  });

  function handleOptionSelect(qIdx, qObj, optObj, cardElem) {
    triggerHaptic();
    playPop();

    // Visual selection feedback
    const allCards = quizOptionsContainer.querySelectorAll('.quiz-option-card');
    allCards.forEach(c => c.classList.remove('selected'));
    cardElem.classList.add('selected');

    // Save answer with persistence
    state.answers[qIdx] = {
      qIdx: qIdx,
      qText: qObj.question,
      optText: optObj.text,
      scoreVal: optObj.score
    };

    // Show reaction toast
    quizReactionText.textContent = optObj.reaction;
    quizReactionBubble.classList.add('visible');

    // Advance smoothly
    setTimeout(() => {
      if (qIdx + 1 < QUIZ_QUESTIONS.length) {
        state.currentQuizIndex = qIdx + 1;
        renderQuizQuestion(state.currentQuizIndex);
      } else {
        // Complete Quiz -> Calculate Initial Score
        playChime();
        calculateInitialScore();
        showScreen('initialScore');
      }
    }, 600);
  }

  // --- Screen 3: Calculate & Render Initial Score ---
  function calculateInitialScore() {
    let totalScore = 0;
    state.answers.forEach(a => {
      totalScore += (a ? a.scoreVal : 10.0);
    });
    state.quizScore = Math.min(100, Math.round(totalScore));
    state.initialBand = getResultBand(state.quizScore);

    initialScoreNum.textContent = state.quizScore;
    initialScoreBar.style.width = `${state.quizScore}%`;
    initialScoreBand.textContent = state.initialBand;
    initialScoreDesc.textContent = getBandDescription(state.initialBand);

    // Save initial session state to backend
    fetch('/api/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sessionId: state.sessionId,
        playerAlias: state.playerAlias,
        quizScore: state.quizScore,
        resultBand: state.initialBand,
        answers: state.answers
      })
    }).catch(() => {
      // Offline fallback: purely client-side
    });
  }

  btnToDistanceChallenge.addEventListener('click', () => {
    triggerHaptic();
    playPop();
    showScreen('distanceChallenge');
  });

  // --- Screen 4: Distance Challenge ---
  btnBackToScore.addEventListener('click', () => {
    triggerHaptic();
    playPop();
    showScreen('initialScore');
  });

  btnCalcDistance.addEventListener('click', () => {
    triggerHaptic();
    playPop();
    requestLocationAndCalculateDistance();
  });

  btnDistanceRetry.addEventListener('click', () => {
    triggerHaptic();
    playPop();
    requestLocationAndCalculateDistance();
  });

  function requestLocationAndCalculateDistance() {
    distanceStatusBox.style.display = 'flex';
    distanceSpinner.style.display = 'inline-block';
    distanceStatusText.textContent = 'Requesting device GPS with high accuracy...';
    btnDistanceRetry.style.display = 'none';
    distanceResultCard.style.display = 'none';
    distanceContinueBar.style.display = 'none';

    if (!('geolocation' in navigator)) {
      distanceSpinner.style.display = 'none';
      distanceStatusText.textContent = 'Geolocation not supported on this browser.';
      btnDistanceRetry.style.display = 'inline-block';
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        const accuracy = Math.round(position.coords.accuracy || 20);
        const timestamp = new Date().toISOString();

        state.hasLocationConsent = true;
        state.locationPermission = 'granted';
        state.locationData = {
          latitude: lat,
          longitude: lon,
          accuracy: accuracy,
          timestamp: timestamp
        };

        // Send to backend endpoint for distance calculation against configured Prajwal reference coords
        fetch('/api/calculate-distance', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sessionId: state.sessionId,
            latitude: lat,
            longitude: lon,
            accuracy: accuracy,
            consent: true
          })
        })
        .then(res => res.json())
        .then(data => {
          if (data.error) {
            handleDistanceError(data.error);
            return;
          }
          handleDistanceSuccess(data.distanceKm, data.distanceDisplay, data.distanceScore, data.distanceCaption);
        })
        .catch(() => {
          // Fallback client-side calculation if running standalone without backend
          const prajwalLat = 13.103691;
          const prajwalLon = 77.570392;
          const dKm = clientHaversine(lat, lon, prajwalLat, prajwalLon);
          let dScore = 20;
          if (dKm <= 5) dScore = 100;
          else if (dKm <= 25) dScore = 80;
          else if (dKm <= 100) dScore = 60;
          else if (dKm <= 300) dScore = 40;

          let caption = "Bakbak sathi kilometres don't matter.";
          if (dKm <= 25) caption = "Arey, almost same area! Chai break banto.";
          else if (dKm <= 300) caption = "Thoda travel tar banta hai. Road trip energy!";

          const display = dKm < 1 ? `${Math.round(dKm * 1000)} m` : `${dKm.toFixed(1)} km`;
          handleDistanceSuccess(dKm, display, dScore, caption);
        });
      },
      (error) => {
        distanceSpinner.style.display = 'none';
        btnDistanceRetry.style.display = 'inline-block';
        if (error.code === error.PERMISSION_DENIED) {
          distanceStatusText.textContent = 'Location permission denied by browser. Please enable GPS in device settings and retry.';
        } else if (error.code === error.TIMEOUT) {
          distanceStatusText.textContent = 'GPS measurement timed out. Please check your signal and tap Retry.';
        } else {
          distanceStatusText.textContent = 'Location unavailable on your device. Please retry.';
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 12000,
        maximumAge: 30000
      }
    );
  }

  function clientHaversine(lat1, lon1, lat2, lon2) {
    const R = 6371.0;
    const toRad = Math.PI / 180;
    const dLat = (lat2 - lat1) * toRad;
    const dLon = (lon2 - lon1) * toRad;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(lat1 * toRad) * Math.cos(lat2 * toRad) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  function handleDistanceSuccess(distKm, displayStr, distScore, caption) {
    playChime();
    distanceStatusBox.style.display = 'none';
    btnCalcDistance.style.display = 'none';
    btnBackToScore.style.display = 'none';

    state.distanceKm = distKm;
    state.distanceDisplay = displayStr;
    state.distanceScore = distScore;
    state.distanceCaption = caption;

    distanceValText.textContent = `${displayStr} apart`;
    distanceCaptionText.textContent = caption;
    distanceResultCard.style.display = 'block';
    distanceContinueBar.style.display = 'flex';
  }

  function handleDistanceError(err) {
    distanceSpinner.style.display = 'none';
    distanceStatusText.textContent = err || 'Distance calculation error.';
    btnDistanceRetry.style.display = 'inline-block';
  }

  // --- Screen 5: Final Score (80% Quiz + 20% Distance) ---
  btnToFinalScore.addEventListener('click', () => {
    triggerHaptic();
    playChime();
    calculateAndRenderFinalScore();
    showScreen('finalScore');
  });

  function calculateAndRenderFinalScore() {
    // Final score = round((Quiz score × 0.80) + (Distance score × 0.20))
    const quizWeight = 0.80;
    const distWeight = 0.20;
    const qScore = state.quizScore;
    const dScore = state.distanceScore !== null ? state.distanceScore : 80;

    const quizContrib = (qScore * quizWeight);
    const distContrib = (dScore * distWeight);
    const finalVal = Math.max(0, Math.min(100, Math.round(quizContrib + distContrib)));

    state.finalScore = finalVal;
    state.finalBand = getResultBand(finalVal);

    finalScoreNum.textContent = finalVal;
    finalScoreBar.style.width = `${finalVal}%`;
    finalScoreBand.textContent = state.finalBand;
    finalScoreDesc.textContent = getBandDescription(state.finalBand);

    breakdownQuizVal.textContent = `${qScore} pts`;
    breakdownQuizContrib.textContent = `+${quizContrib.toFixed(1)} pts`;
    breakdownDistVal.textContent = `${dScore} pts`;
    breakdownDistContrib.textContent = `+${distContrib.toFixed(1)} pts`;
  }

  btnToVacationChallenge.addEventListener('click', () => {
    triggerHaptic();
    playPop();
    renderVacationRecommendation();
    showScreen('vacationChallenge');
  });

  // --- Screen 6: Combined Vacation + Location Challenge Screen ---
  function renderVacationRecommendation() {
    // Select curated vacation based on answers and score
    let vacIdx = 0;
    if (state.answers[0] && state.answers[0].optText.includes('drive')) {
      vacIdx = 1; // Beach / Road trip
    } else if (state.answers[0] && state.answers[0].optText.includes('Gharich')) {
      vacIdx = 0; // Lonavala chill
    } else if (state.finalScore >= 85) {
      vacIdx = 2; // FC Road / KP Pune
    } else {
      vacIdx = 3; // Tamhini Ghat
    }

    const vac = VACATIONS[vacIdx];
    postcardIcon.textContent = vac.icon;
    postcardTitle.textContent = vac.title;
    postcardTagline.textContent = vac.tagline;
    postcardDesc.textContent = vac.desc;
    postcardWhyText.textContent = vac.why;
  }

  // Go for it♡ - Location challenge button inside combined screen
  btnGoForIt.addEventListener('click', () => {
    triggerHaptic();
    playPop();

    // Check explicit consent checkbox
    if (!consentAgreementChk.checked) {
      showToast("Please check the agreement box to share location ♡");
      return;
    }

    challengeStatusBox.style.display = 'flex';
    challengeSpinner.style.display = 'inline-block';
    challengeStatusText.textContent = 'Transmitting consented location measurement to Prajwal...';
    btnChallengeRetry.style.display = 'none';

    // If we already have a valid consented measurement from this session, submit it
    if (state.locationData && state.hasLocationConsent) {
      submitConsentedLocation(state.locationData);
    } else {
      // Request fresh measurement
      if (!('geolocation' in navigator)) {
        challengeSpinner.style.display = 'none';
        challengeStatusText.textContent = 'Geolocation not supported on this device.';
        btnChallengeRetry.style.display = 'inline-block';
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const lat = pos.coords.latitude;
          const lon = pos.coords.longitude;
          const acc = Math.round(pos.coords.accuracy || 20);
          const ts = new Date().toISOString();

          state.hasLocationConsent = true;
          state.locationData = {
            latitude: lat,
            longitude: lon,
            accuracy: acc,
            timestamp: ts
          };
          submitConsentedLocation(state.locationData);
        },
        (err) => {
          challengeSpinner.style.display = 'none';
          btnChallengeRetry.style.display = 'inline-block';
          challengeStatusText.textContent = 'Location acquisition failed: ' + (err.message || 'Permission denied.');
        },
        { enableHighAccuracy: true, timeout: 12000, maximumAge: 10000 }
      );
    }
  });

  btnChallengeRetry.addEventListener('click', () => {
    triggerHaptic();
    playPop();
    btnGoForIt.click();
  });

  function submitConsentedLocation(loc) {
    fetch('/api/location', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sessionId: state.sessionId,
        latitude: loc.latitude,
        longitude: loc.longitude,
        accuracy: loc.accuracy,
        consent: true,
        consentTimestamp: loc.timestamp
      })
    })
    .then(res => res.json())
    .then(data => {
      challengeStatusBox.style.display = 'none';
      btnGoForIt.style.display = 'none';
      consentAgreementChk.parentElement.style.display = 'none';

      // Show Cheerful Reveal on the same screen!
      coordsText.textContent = `Lat: ${loc.latitude.toFixed(4)}°, Lon: ${loc.longitude.toFixed(4)}°`;
      coordsAccuracy.textContent = `Reported horizontal accuracy: ±${loc.accuracy} metres`;
      mapLinkBtn.href = `https://www.openstreetmap.org/?mlat=${loc.latitude}&mlon=${loc.longitude}#map=14/${loc.latitude}/${loc.longitude}`;

      revealSuccessBox.style.display = 'block';
      playVictoryFanfare();
      startConfetti();
    })
    .catch(() => {
      // Local demo mode fallback
      challengeStatusBox.style.display = 'none';
      btnGoForIt.style.display = 'none';
      coordsText.textContent = `Lat: ${loc.latitude.toFixed(4)}°, Lon: ${loc.longitude.toFixed(4)}°`;
      coordsAccuracy.textContent = `Reported horizontal accuracy: ±${loc.accuracy} metres`;
      mapLinkBtn.href = `https://www.openstreetmap.org/?mlat=${loc.latitude}&mlon=${loc.longitude}`;
      revealSuccessBox.style.display = 'block';
      playVictoryFanfare();
      startConfetti();
    });
  }

  // Copy Friendship Dossier
  btnCopySummary.addEventListener('click', () => {
    triggerHaptic();
    playChime();

    const text = [
      `☕ FRIENDSHIP METER DOSSIER ☕`,
      `Player: ${state.playerAlias}`,
      `Initial Quiz Score: ${state.quizScore}/100`,
      `Distance to Prajwal: ${state.distanceDisplay || 'Measured'} (${state.distanceCaption})`,
      `Final Score (80% Quiz + 20% Distance): ${state.finalScore}/100`,
      `Result Band: ${state.finalBand}`,
      `Getaway Match: ${postcardTitle.textContent}`,
      `Status: hehe, challenge completed ♡`,
      `Bragging rights: acquired.`
    ].join('\n');

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        showToast("Friendship Dossier copied! Send it to Prajwal 💌");
      }).catch(() => fallbackCopy(text));
    } else {
      fallbackCopy(text);
    }
  });

  function fallbackCopy(text) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand('copy');
      showToast("Dossier copied to clipboard! 💌");
    } catch (e) {
      showToast("Screenshot this card to share! 📸");
    }
    document.body.removeChild(ta);
  }

  btnPlayAgain.addEventListener('click', () => {
    triggerHaptic();
    playPop();
    state.sessionId = 'fm_' + Math.random().toString(36).substring(2, 10);
    state.currentQuizIndex = 0;
    state.answers = [];
    state.quizScore = 0;
    state.distanceKm = null;
    state.distanceScore = null;
    state.finalScore = null;

    btnCalcDistance.style.display = 'flex';
    btnBackToScore.style.display = 'block';
    distanceResultCard.style.display = 'none';
    distanceContinueBar.style.display = 'none';

    btnGoForIt.style.display = 'flex';
    consentAgreementChk.parentElement.style.display = 'block';
    revealSuccessBox.style.display = 'none';

    showScreen('welcome');
  });

  function showToast(msg) {
    let toast = document.querySelector('.toast-msg');
    if (!toast) {
      toast = document.createElement('div');
      toast.className = 'toast-msg';
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
  }

  // --- Canvas Confetti Engine ---
  let confettiAnimId = null;
  function startConfetti() {
    if (!confettiCanvas) return;
    const ctx = confettiCanvas.getContext('2d');
    const width = confettiCanvas.width = confettiCanvas.offsetWidth || 380;
    const height = confettiCanvas.height = confettiCanvas.offsetHeight || 600;

    const colors = ['#F6DCE5', '#DCD5F7', '#F6E8A8', '#65536B', '#FFF8F0'];
    const particles = [];
    for (let i = 0; i < 48; i++) {
      particles.push({
        x: width * 0.5 + (Math.random() - 0.5) * 60,
        y: height * 0.4,
        vx: (Math.random() - 0.5) * 7,
        vy: -Math.random() * 5 - 2,
        size: Math.random() * 6 + 4,
        color: colors[Math.floor(Math.random() * colors.length)],
        rotation: Math.random() * 360,
        vr: (Math.random() - 0.5) * 8,
        gravity: 0.18,
        drag: 0.98,
        shape: Math.random() > 0.4 ? 'circle' : 'rect'
      });
    }

    if (confettiAnimId) cancelAnimationFrame(confettiAnimId);

    let frame = 0;
    function render() {
      ctx.clearRect(0, 0, width, height);
      particles.forEach(p => {
        p.vx *= p.drag;
        p.vy = (p.vy + p.gravity) * p.drag;
        p.x += p.vx;
        p.y += p.vy;
        p.rotation += p.vr;

        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate((p.rotation * Math.PI) / 180);
        ctx.fillStyle = p.color;

        if (p.shape === 'circle') {
          ctx.beginPath();
          ctx.arc(0, 0, p.size / 2, 0, Math.PI * 2);
          ctx.fill();
        } else {
          ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.7);
        }
        ctx.restore();
      });

      frame++;
      if (frame < 180) {
        confettiAnimId = requestAnimationFrame(render);
      } else {
        ctx.clearRect(0, 0, width, height);
      }
    }
    render();
  }

  window.addEventListener('resize', () => {
    if (confettiCanvas) {
      confettiCanvas.width = confettiCanvas.offsetWidth;
      confettiCanvas.height = confettiCanvas.offsetHeight;
    }
  });

  // Default initial screen
  showScreen('welcome');

})();
