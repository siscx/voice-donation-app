// translations.js - All translation data for the voice donation app

const translations = {
    en: {
        // Hero Section
        heroTitle: "Donate Your Voice For Health",
        heroSubtitle: "Help us unlock the potential of voice for early health detection. Your donation helps train AI to identify signs of chronic conditions in under 3 minutes of voice recordings—building proactive healthcare for everyone.",

        // Step 1 - Welcome
        step1Title: "Your Voice, Our Future",
        step1Text: "Every voice carries hidden health insights. Your unique vocal patterns hold clues that could transform how we detect and prevent illness. Help us build the foundation for accessible healthcare worldwide.",
        stat1Number: "60+",
        stat1Label: "Voice features analyzed",
        stat2Number: "3min",
        stat2Label: "Time to contribute",
        step1Button: "Begin Your Contribution",

        // Step 2 - Questionnaire
        step2Title: "Health Questionnaire",
        step2Subtitle: "Anonymous data helps train our AI models",

        // Basic Form Fields
        donationLanguageLabel: "Recording Language",
        donationLanguageSelect: "Select the language for your voice recording",
        donationLanguageEnglish: "English",
        donationLanguageArabic: "Arabic",
        ageLabel: "Age Range",
        ageSelect: "Select your age range",
        age1825: "18-25 years",
        age2635: "26-35 years",
        age3645: "36-45 years",
        age4655: "46-55 years",
        age5665: "56-65 years",
        age6675: "66-75 years",
        age76plus: "76+ years",

        // Language/Dialect Fields
        nativeLanguageLabel: "What is your native language?",
        nativeLanguageSelect: "Select your native language",
        arabicDialectLabel: "Which Arabic dialect do you speak?",
        arabicDialectSelect: "Select your Arabic dialect",
        arabicDialectEgyptian: "Egyptian Arabic",
        arabicDialectLevantine: "Levantine Arabic",
        arabicDialectGulf: "Gulf Arabic (Khaleeji)",
        arabicDialectMaghrebi: "Maghrebi Arabic",
        arabicDialectIraqi: "Iraqi Arabic",
        arabicDialectSudanese: "Sudanese Arabic",
        arabicDialectYemeni: "Yemeni Arabic",
        arabicDialectHejazi: "Hejazi Arabic",
        arabicDialectNajdi: "Najdi Arabic",
        arabicDialectMSA: "Modern Standard Arabic (MSA)",

        // Health Conditions
        conditionsLabel: "Health Conditions",
        conditionsHelper: "Select all conditions that apply to you and indicate their severity",
        conditionNone: "None - I have no diagnosed health conditions",

        // Categories
        categoryNeurological: "Neurological Conditions",
        categoryRespiratory: "Respiratory Conditions",
        categoryMood: "Mood and Psychiatric Conditions",
        categoryMetabolic: "Metabolic/Endocrine Conditions",
        categoryVoice: "Voice Problems",

        // Neurological Conditions
        conditionAlzheimers: "Alzheimer's",
        conditionDementia: "Dementia",
        conditionMCI: "Mild Cognitive Impairment",
        conditionALS: "ALS",
        conditionHuntingtons: "Huntington's disease",
        conditionParkinsons: "Parkinson's disease",

        // Respiratory Conditions
        conditionAsthma: "Asthma",
        conditionChronicCough: "Chronic cough",
        conditionCOPD: "COPD",
        conditionRespiratoryOther: "Other respiratory condition",

        // Mood/Psychiatric Conditions
        conditionDepression: "Depression disorder",
        conditionAnxiety: "Anxiety disorder",
        conditionSubstanceUse: "Alcohol or substance use disorder",
        conditionBipolar: "Bipolar disorder",
        conditionAutism: "Autism spectrum disorder",
        conditionADHD: "ADHD",
        conditionMoodOther: "Other mood/psychiatric condition",

        // Metabolic/Endocrine Conditions
        conditionDiabetes1: "Diabetes type 1",
        conditionDiabetes2: "Diabetes type 2",
        conditionPrediabetes: "Prediabetes",
        conditionThyroid: "Thyroid Disorder",
        conditionObesity: "Obesity",

        // Voice Problems
        conditionVocalFoldParalysis: "Unilateral vocal fold paralysis",
        conditionMuscleTensionDysphonia: "Muscle Tension Dysphonia",
        conditionSpasmodicDysphonia: "Spasmodic Dysphonia/laryngeal tremor",
        conditionVocalLesions: "Lesions (vocal polyp, nodules etc)",
        conditionLaryngitis: "Laryngitis",
        conditionLaryngealCancer: "Laryngeal cancer",
        conditionVoiceOther: "Other voice problem",

        // Other Conditions
        conditionOtherGeneral: "Other condition (please specify)",
        otherGeneralConditionLabel: "Please specify your condition",
        otherGeneralConditionPlaceholder: "Describe your condition",

        // Severity Options
        severitySelect: "Select severity",
        severityMild: "Mild",
        severityMedium: "Medium",
        severitySevere: "Severe",
        severityUnknown: "I do not know",

        // Specification Placeholders
        specifyRespiratoryOtherPlaceholder: "Please specify your respiratory condition",
        specifyMoodOtherPlaceholder: "Please specify your mood/psychiatric condition",
        specifyVoiceOtherPlaceholder: "Please specify your voice problem",

        continueButton: "Continue to Voice Recording",

        // Step 3 - Recording
        step3Title: "Voice Recording",
        taskProgress: "Task 1 of 3",
        recordingInstructions: "Please speak about 20 cm (8 inches) from your device's microphone, in a quiet environment if possible.",

        // Task 1: Maximum Phonation Time
        task1Subtitle: "Say 'ahhh' (like /e/ sound) for as long as you can. Try to sustain the sound steadily.",
        task1Question: "Maximum Phonation Time Test",
        task1Instruction: "Take a deep breath and say 'ahhh' for as long as you can. Keep the sound steady and continuous until you run out of breath.",

        // Task 2: Picture Description
        task2Subtitle: "Please describe what you see in the image below. Speak naturally for at least 30 seconds.",
        task2Instruction: "Describe what you see in this image - the people, activities, setting, and any details you notice.",

        // Task 3: Weekend Question
        task3Subtitle: "Please describe your perfect weekend. Speak naturally for at least 30 seconds, up to 1 minute.",
        task3Question: "What does your perfect weekend look like?",
        task3Instruction: "Describe your ideal weekend - activities you'd enjoy, places you'd go, people you'd spend time with, and what would make it special for you.",

        // Recording Controls
        recordingStatusStart: "Click to start recording",
        recordingStatusRecording: "Recording... Click to stop",
        recordingStatusComplete: "Recording complete!",
        continueToTask2: "Continue to Next Task",
        submitAllTasks: "Submit Voice Donation",
        consentText: "By submitting, you grant consent for anonymous use of your voice recordings in health research, with data stored securely indefinitely for ongoing scientific analysis.",

        // Processing (UPDATED for background processing)
        processingTitle: "Submitting Your Voice Donation",
        processingSubtitle: "Preparing Your Recordings",
        processingDescription: "Your voice recordings are being submitted for medical research. This will only take a moment.",
        processingStatus: "Submitting your voice donation...",
        processingWait: "Please wait while we process your submission.",
        feature1: "✓ Pitch patterns",
        feature2: "✓ Voice quality",
        feature3: "✓ Speech rhythm",
        feature4: "✓ Spectral features",
        feature5: "✓ Intensity measures",
        feature6: "✓ Formant frequencies",

        // Success (UPDATED for background processing)
        successIcon: "🎉",
        successTitle: "Thank You!",
        successSubtitle: "Your voice recordings have been submitted successfully and are being processed to advance medical research.",
        successDescription: "You can safely close this page. Your anonymous donation contributes to developing AI that can detect health conditions years before symptoms appear, bringing proactive healthcare within reach for everyone.",
        privacyNote: "Your data is stored securely and used anonymously for health research. To request removal of your donation, please email info@munsait.com and include your Donation ID above for faster processing.",

        // Tab Navigation
        tabHome: "Home",
        tabAbout: "About Us",
        tabScience: "The Science",

        // About Us Tab
        aboutTitle: "Who We Are",
        aboutContent: "We're a team of clinicians, scientists, and technologists on a mission to make healthcare more accessible and proactive. With deep experience in Voice, health, and AI, we're building tools that can detect subtle changes in your voice to support early screening and remote monitoring. We believe your voice holds powerful clues about your health—and that with the right safeguards, it can help transform care for millions.",
        aboutContent2: "This app is part of that vision. Every voice shared brings us closer to safer, smarter, and more inclusive health solutions.",

        // Science Tab
        scienceTitle: "The Science Behind Voice Biomarkers",
        scienceIntro: "Your voice is more than just sound—it reflects how your body and brain are doing.",
        scienceResearch: "Research from institutions like Mayo Clinic, MIT, and the NIH has shown that subtle changes in voice—such as pitch, rhythm, pauses, and breathiness—can reveal early signs of health changes. This field, known as voice biomarker research, is growing quickly and showing real promise.",
        scienceConditions: "Studies have linked voice patterns to a wide range of health conditions, including:",
        conditionRespiratory2: "• Respiratory issues",
        conditionCognitive: "• Cognitive decline",
        conditionNeurological2: "• Neurological disorders",
        conditionCardiovascular2: "• Cardiovascular diseases",
        conditionMental: "• Mental health challenges",
        scienceAI: "By combining voice data with AI, researchers are developing tools that can help detect and monitor health conditions—non-invasively, passively, and at scale.",
        scienceMission: "Your voice donation supports this mission. With just a brief speech sample, you're helping build the science needed to make healthcare more proactive, accessible, and personalized—for everyone.",

        // Testimonials
        testimonial1: '"When I found out that a short voice recording could help researchers detect diseases earlier, I didn\'t hesitate. It felt empowering to know that something so easy for me could be so meaningful for someone else. I donated my voice for science, and I\'d do it again in a heartbeat."',
        testimonial1Author: "- Jamal, 65 years old, UAE",
        testimonial2: '"It\'s incredible to think my voice could help someone track their health better. I love knowing I\'m part of a project that could change how we fight chronic illness in our region."',
        testimonial2Author: "- Salma, 43 years old, Morocco",
        testimonial3: '"Your voice holds more health information than you imagine. With just a brief audio sample, we can begin to detect patterns linked to chronic diseases. But for our research to be accurate and inclusive, we need thousands of voices—different ages, accents, and health backgrounds."',
        testimonial3Author: "- Dr Leila, Neurologist",
        testimonial4: '"Most of the medical AI tools today are trained on data from outside our region. But voice, like language and accent, varies across populations. By donating your voice, you\'re helping us build healthcare solutions that truly reflect and serve our communities."',
        testimonial4Author: "- Dr Ahmed, Pulmonologist",

        // Research tab
        tabResearch: "Key Studies",
        researchTitle: "Key Studies on Voice Biomarkers",
        researchIntroTitle: "Scientific Foundation",
        researchIntroText: "Voice biomarker research is rapidly advancing, with studies from leading institutions demonstrating the potential of vocal analysis for health monitoring. Here are key publications that form the scientific foundation of our work.",
        viewPaper: "View Paper"
    },

    ar: {
        // Hero Section
        heroTitle: "تبرع بصوتك من أجل الصحة",
        heroSubtitle: "ساعدنا في إطلاق إمكانات الصوت للكشف المبكر عن الصحة. يساعد تبرعك في تدريب الذكاء الاصطناعي على تحديد علامات الحالات المزمنة في أقل من 3 دقائق من التسجيلات الصوتية—لبناء رعاية صحية استباقية للجميع.",

        // Step 1 - Welcome
        step1Title: "صوتك، مستقبلنا",
        step1Text: "كل صوت يحمل رؤى صحية مخفية. تحمل أنماطك الصوتية الفريدة أدلة يمكن أن تحول كيفية اكتشافنا ومنعنا للمرض. ساعدنا في بناء الأساس للرعاية الصحية المتاحة عالمياً.",
        stat1Number: "60+",
        stat1Label: "ميزات صوتية تم تحليلها",
        stat2Number: "3 دقائق",
        stat2Label: "الوقت المطلوب للمساهمة",
        step1Button: "ابدأ بالمساهمة",

        // Step 2 - Questionnaire
        step2Title: "الاستبيان الصحي",
        step2Subtitle: "البيانات المجهولة تساعد في تدريب نماذج الذكاء الاصطناعي",

        // Basic Form Fields
        donationLanguageLabel: "لغة التسجيل",
        donationLanguageSelect: "اختر لغة تسجيلك الصوتي",
        donationLanguageEnglish: "الإنجليزية",
        donationLanguageArabic: "العربية",
        ageLabel: "الفئة العمرية",
        ageSelect: "اختر فئتك العمرية",
        age1825: "18-25 سنة",
        age2635: "26-35 سنة",
        age3645: "36-45 سنة",
        age4655: "46-55 سنة",
        age5665: "56-65 سنة",
        age6675: "66-75 سنة",
        age76plus: "76+ سنة",

        // Language/Dialect Fields
        nativeLanguageLabel: "ما هي لغتك الأم؟",
        nativeLanguageSelect: "اختر لغتك الأم",
        arabicDialectLabel: "ما هي اللهجة العربية التي تتحدث بها؟",
        arabicDialectSelect: "اختر لهجتك العربية",
        arabicDialectEgyptian: "العربية المصرية",
        arabicDialectLevantine: "العربية الشامية",
        arabicDialectGulf: "العربية الخليجية",
        arabicDialectMaghrebi: "العربية المغاربية",
        arabicDialectIraqi: "العربية العراقية",
        arabicDialectSudanese: "العربية السودانية",
        arabicDialectYemeni: "العربية اليمنية",
        arabicDialectHejazi: "العربية الحجازية",
        arabicDialectNajdi: "العربية النجدية",
        arabicDialectMSA: "العربية الفصحى الحديثة",

        // Health Conditions
        conditionsLabel: "الحالات الصحية",
        conditionsHelper: "اختر كل الحالات التي تنطبق عليك وحدد شدتها",
        conditionNone: "لا يوجد - ليس لدي أي حالات صحية مشخصة",

        // Categories
        categoryNeurological: "الحالات العصبية",
        categoryRespiratory: "الحالات التنفسية",
        categoryMood: "حالات المزاج والطب النفسي",
        categoryMetabolic: "حالات التمثيل الغذائي/الغدد الصماء",
        categoryVoice: "مشاكل الصوت",

        // Neurological Conditions
        conditionAlzheimers: "الزهايمر",
        conditionDementia: "الخرف",
        conditionMCI: "ضعف إدراكي خفيف",
        conditionALS: "التصلب الجانبي الضموري",
        conditionHuntingtons: "مرض هنتنغتون",
        conditionParkinsons: "مرض باركنسون",

        // Respiratory Conditions
        conditionAsthma: "الربو",
        conditionChronicCough: "السعال المزمن",
        conditionCOPD: "مرض الانسداد الرئوي المزمن",
        conditionRespiratoryOther: "حالة تنفسية أخرى",

        // Mood/Psychiatric Conditions
        conditionDepression: "اضطراب الاكتئاب",
        conditionAnxiety: "اضطراب القلق",
        conditionSubstanceUse: "اضطراب تعاطي الكحول أو المواد",
        conditionBipolar: "اضطراب ثنائي القطب",
        conditionAutism: "اضطراب طيف التوحد",
        conditionADHD: "اضطراب نقص الانتباه وفرط النشاط",
        conditionMoodOther: "حالة مزاج/نفسية أخرى",

        // Metabolic/Endocrine Conditions
        conditionDiabetes1: "السكري من النوع الأول",
        conditionDiabetes2: "السكري من النوع الثاني",
        conditionPrediabetes: "مقدمات السكري",
        conditionThyroid: "اضطراب الغدة الدرقية",
        conditionObesity: "السمنة",

        // Voice Problems
        conditionVocalFoldParalysis: "شلل الحبل الصوتي الأحادي",
        conditionMuscleTensionDysphonia: "خلل النطق بتوتر العضلات",
        conditionSpasmodicDysphonia: "خلل النطق التشنجي/رعشة الحنجرة",
        conditionVocalLesions: "آفات (لحمية صوتية، عقد إلخ)",
        conditionLaryngitis: "التهاب الحنجرة",
        conditionLaryngealCancer: "سرطان الحنجرة",
        conditionVoiceOther: "مشكلة صوتية أخرى",

        // Other Conditions
        conditionOtherGeneral: "حالة أخرى (يرجى التحديد)",
        otherGeneralConditionLabel: "يرجى تحديد حالتك",
        otherGeneralConditionPlaceholder: "اوصف حالتك",

        // Severity Options
        severitySelect: "اختر الشدة",
        severityMild: "خفيف",
        severityMedium: "متوسط",
        severitySevere: "شديد",
        severityUnknown: "لا أعرف",

        // Specification Placeholders
        specifyRespiratoryOtherPlaceholder: "يرجى تحديد حالتك التنفسية",
        specifyMoodOtherPlaceholder: "يرجى تحديد حالتك النفسية/المزاجية",
        specifyVoiceOtherPlaceholder: "يرجى تحديد مشكلتك الصوتية",

        continueButton: "المتابعة إلى تسجيل الصوت",

        // Step 3 - Recording
        step3Title: "تسجيل الصوت",
        taskProgress: "المهمة 1 من 3",
        recordingInstructions: "يرجى التحدث على بُعد حوالي 20 سم (8 بوصات) من ميكروفون جهازك، في بيئة هادئة إن أمكن.",

        // Task 1: Maximum Phonation Time
        task1Subtitle: "قل 'آآآه' (مثل صوت /e/) لأطول فترة ممكنة. حاول الحفاظ على الصوت ثابتاً ومستمراً.",
        task1Question: "اختبار أقصى زمن للنطق",
        task1Instruction: "خذ نفساً عميقاً وقل 'آآآه' لأطول فترة ممكنة. حافظ على الصوت ثابتاً ومستمراً حتى ينتهي نفسك.",

        // Task 2: Picture Description
        task2Subtitle: "يرجى وصف ما تراه في الصورة أدناه. تحدث بشكل طبيعي لمدة 30 ثانية على الأقل.",
        task2Instruction: "صف ما تراه في هذه الصورة - الأشخاص والأنشطة والبيئة وأي تفاصيل تلاحظها.",

        // Task 3: Weekend Question
        task3Subtitle: "يرجى وصف عطلة نهاية الأسبوع المثالية لك. تحدث بشكل طبيعي لمدة 30 ثانية على الأقل، وحتى دقيقة واحدة.",
        task3Question: "كيف تبدو عطلة نهاية الأسبوع المثالية لك؟",
        task3Instruction: "صف عطلة نهاية الأسبوع المثالية لك - الأنشطة التي ستستمتع بها، والأماكن التي ستذهب إليها، والأشخاص الذين ستقضي الوقت معهم، وما الذي سيجعلها مميزة بالنسبة لك.",

        // Recording Controls
        recordingStatusStart: "اضغط لبدء التسجيل",
        recordingStatusRecording: "جاري التسجيل... اضغط للتوقف",
        recordingStatusComplete: "اكتمل التسجيل!",
        continueToTask2: "المتابعة إلى المهمة التالية",
        submitAllTasks: "أرسل التبرع الصوتي",
        consentText: "من خلال الإرسال، فإنك توافق على الاستخدام المجهول لتسجيلاتك الصوتية في الأبحاث الصحية، مع تخزين البيانات بشكل آمن إلى أجل غير مسمى للتحليل العلمي المستمر.",

        // Processing (UPDATED for background processing)
        processingTitle: "إرسال تبرعك الصوتي",
        processingSubtitle: "تحضير تسجيلاتك",
        processingDescription: "جاري إرسال تسجيلاتك الصوتية للبحوث الطبية. سيستغرق هذا لحظة فقط.",
        processingStatus: "جاري إرسال تبرعك الصوتي...",
        processingWait: "يرجى الانتظار بينما نعالج إرسالك.",
        feature1: "✓ أنماط الطبقة الصوتية",
        feature2: "✓ جودة الصوت",
        feature3: "✓ إيقاع الكلام",
        feature4: "✓ الميزات الطيفية",
        feature5: "✓ قياسات الشدة",
        feature6: "✓ ترددات التكوين",

        // Success (UPDATED for background processing)
        successIcon: "🎉",
        successTitle: "شكراً لك!",
        successSubtitle: "تم إرسال تسجيلاتك الصوتية بنجاح وجاري معالجتها لتطوير البحوث الطبية.",
        successDescription: "يمكنك إغلاق هذه الصفحة بأمان. يساهم تبرعك المجهول في تطوير ذكاء اصطناعي يمكنه اكتشاف الحالات الصحية قبل سنوات من ظهور الأعراض، مما يجعل الرعاية الصحية الاستباقية في متناول الجميع.",
        privacyNote: "يتم تخزين بياناتك بأمان واستخدامها بشكل مجهول للبحوث الصحية. لطلب إزالة تبرعك، يرجى مراسلة info@munsait.com وتضمين معرف التبرع أعلاه لمعالجة أسرع.",

        // Tab Navigation
        tabHome: "الرئيسية",
        tabAbout: "من نحن",
        tabScience: "العلم",

        // About Us Tab
        aboutTitle: "من نحن",
        aboutContent: "نحن فريق من الأطباء والعلماء والتقنيين في مهمة لجعل الرعاية الصحية أكثر إتاحة واستباقية. مع خبرة عميقة في الصوت والصحة والذكاء الاصطناعي، نحن نبني أدوات يمكنها اكتشاف التغييرات الدقيقة في صوتك لدعم الفحص المبكر والمراقبة عن بُعد. نحن نؤمن أن صوتك يحمل أدلة قوية حول صحتك—وأنه مع الضمانات المناسبة، يمكن أن يساعد في تحويل الرعاية لملايين الأشخاص.",
        aboutContent2: "هذا التطبيق جزء من تلك الرؤية. كل صوت يتم مشاركته يقربنا من حلول صحية أكثر أماناً وذكاءً وشمولاً.",

        // Science Tab
        scienceTitle: "العلم وراء المؤشرات الحيوية الصوتية",
        scienceIntro: "صوتك أكثر من مجرد صوت—إنه يعكس كيف يعمل جسمك ودماغك.",
        scienceResearch: "أظهرت الأبحاث من مؤسسات مثل مايو كلينك وإم آي تي والمعاهد الوطنية للصحة أن التغييرات الدقيقة في الصوت—مثل النبرة والإيقاع والتوقفات وضيق التنفس—يمكن أن تكشف عن علامات مبكرة للتغييرات الصحية. هذا المجال، المعروف باسم بحث المؤشرات الحيوية الصوتية، ينمو بسرعة ويظهر وعداً حقيقياً.",
        scienceConditions: "ربطت الدراسات بين أنماط الصوت ومجموعة واسعة من الحالات الصحية، بما في ذلك:",
        conditionRespiratory2: "• مشاكل تنفسية",
        conditionCognitive: "• تراجع إدراكي",
        conditionNeurological2: "• اضطرابات عصبية",
        conditionCardiovascular2: "• أمراض القلب والأوعية الدموية",
        conditionMental: "• تحديات الصحة النفسية",
        scienceAI: "من خلال الجمع بين بيانات الصوت والذكاء الاصطناعي، يطور الباحثون أدوات يمكنها المساعدة في اكتشاف ومراقبة الحالات الصحية—بطريقة غير جراحية وسلبية وعلى نطاق واسع.",
        scienceMission: "تبرعك بالصوت يدعم هذه المهمة. مع تسجيل قصير فقط من الكلام، أنت تساعد في بناء العلم المطلوب لجعل الرعاية الصحية أكثر استباقية وإتاحة وتخصيصاً—للجميع.",

        // Testimonials
        testimonial1: '"عندما اكتشفت أن تسجيل صوتي قصير يمكن أن يساعد الباحثين في اكتشاف الأمراض مبكراً، لم أتردد. شعرت بالتمكين عندما علمت أن شيئاً سهلاً بالنسبة لي يمكن أن يكون مفيداً جداً لشخص آخر. تبرعت بصوتي للعلم، وسأفعل ذلك مرة أخرى دون تردد."',
        testimonial1Author: "- جمال، 65 عاماً، الإمارات",
        testimonial2: '"من المذهل أن أفكر في أن صوتي يمكن أن يساعد شخصاً ما في تتبع صحته بشكل أفضل. أحب معرفة أنني جزء من مشروع يمكن أن يغير كيفية مكافحتنا للأمراض المزمنة في منطقتنا."',
        testimonial2Author: "- سلمى، 43 عاماً، المغرب",
        testimonial3: '"صوتك يحمل معلومات صحية أكثر مما تتخيل. مع عينة صوتية قصيرة فقط، يمكننا البدء في اكتشاف الأنماط المرتبطة بالأمراض المزمنة. لكن لكي يكون بحثنا دقيقاً وشاملاً، نحتاج إلى آلاف الأصوات—أعمار ولهجات وخلفيات صحية مختلفة."',
        testimonial3Author: "- د. ليلى، طبيبة أعصاب",
        testimonial4: '"معظم أدوات الذكاء الاصطناعي الطبية اليوم مدربة على بيانات من خارج منطقتنا. لكن الصوت، مثل اللغة واللهجة، يختلف عبر السكان. من خلال التبرع بصوتك، أنت تساعدنا في بناء حلول رعاية صحية تعكس وتخدم مجتمعاتنا حقاً."',
        testimonial4Author: "- د. أحمد، طبيب رئة",

        // Research tab
        tabResearch: "الدراسات الرئيسية",
        researchTitle: "الدراسات الرئيسية حول المؤشرات الحيوية الصوتية",
        researchIntroTitle: "الأساس العلمي",
        researchIntroText: "تتقدم أبحاث المؤشرات الحيوية الصوتية بسرعة، مع دراسات من مؤسسات رائدة تُظهر إمكانات التحليل الصوتي لمراقبة الصحة. هذه هي المنشورات الرئيسية التي تشكل الأساس العلمي لعملنا.",
        viewPaper: "عرض البحث"
    }
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = translations;
}