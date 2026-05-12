import os
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Module-level sentinel for the lazily-loaded Whisper model.
# Using None as a sentinel (not globals() check) to avoid issues on dev-server restarts.
_whisper_model_instance = None

ACTIVITY_WEIGHTS = {
    "playing": {
        "Social Interaction": 1.4,
        "Repetitive Behaviors": 1.5,
        "Communication": 1.2,
        "Sensory Response": 1.0,
        "Daily Living Skills": 0.8,
        "Emotional Regulation": 1.2,
    },
    "reading": {
        "Communication": 1.5,
        "Repetitive Behaviors": 1.2,
        "Social Interaction": 1.0,
        "Sensory Response": 0.9,
        "Daily Living Skills": 0.8,
        "Emotional Regulation": 1.0,
    },
    "drawing": {
        "Repetitive Behaviors": 1.4,
        "Sensory Response": 1.2,
        "Emotional Regulation": 1.1,
        "Communication": 0.9,
        "Social Interaction": 0.8,
        "Daily Living Skills": 1.0,
    },
    "eating": {
        "Sensory Response": 1.6,
        "Daily Living Skills": 1.4,
        "Emotional Regulation": 1.2,
        "Communication": 0.8,
        "Social Interaction": 0.8,
        "Repetitive Behaviors": 1.0,
    },
    "drinking": {
        "Sensory Response": 1.5,
        "Daily Living Skills": 1.3,
        "Emotional Regulation": 1.1,
        "Communication": 0.8,
        "Social Interaction": 0.8,
        "Repetitive Behaviors": 1.0,
    },
    "writing": {
        "Daily Living Skills": 1.5,
        "Communication": 1.2,
        "Sensory Response": 1.2,
        "Repetitive Behaviors": 1.0,
        "Social Interaction": 0.7,
        "Emotional Regulation": 1.0,
    },
    "social": {
        "Social Interaction": 1.7,
        "Communication": 1.5,
        "Emotional Regulation": 1.3,
        "Repetitive Behaviors": 1.0,
        "Sensory Response": 0.9,
        "Daily Living Skills": 0.8,
    },
}

AGE_MULTIPLIERS = {
    "0-2": {
        "Social Interaction": 0.7,
        "Communication": 0.7,
        "Repetitive Behaviors": 0.8,
        "Sensory Response": 1.0,
        "Daily Living Skills": 0.6,
        "Emotional Regulation": 0.8,
    },
    "3-5": {
        "Social Interaction": 1.0,
        "Communication": 1.0,
        "Repetitive Behaviors": 1.0,
        "Sensory Response": 1.0,
        "Daily Living Skills": 1.0,
        "Emotional Regulation": 1.0,
    },
    "6-9": {
        "Social Interaction": 1.3,
        "Communication": 1.2,
        "Repetitive Behaviors": 1.25,
        "Sensory Response": 1.1,
        "Daily Living Skills": 1.2,
        "Emotional Regulation": 1.2,
    },
    "10+": {
        "Social Interaction": 1.5,
        "Communication": 1.4,
        "Repetitive Behaviors": 1.35,
        "Sensory Response": 1.2,
        "Daily Living Skills": 1.3,
        "Emotional Regulation": 1.3,
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# AUTISM KNOWLEDGE BASE
# Sources: DSM-5, Leo Kanner (1943), Simon Baron-Cohen, Temple Grandin,
# Uta Frith, Jean Ayres, ADOS/ADI-R/CARS clinical tools, ABA/ESDM/PECS
# research, CDC, Autism Speaks, peer-reviewed literature.
# ══════════════════════════════════════════════════════════════════════════════
AUTISM_KNOWLEDGE_BASE = [

    # ── SECTION 1: DSM-5 DIAGNOSTIC CRITERIA ─────────────────────────────────

    "DSM-5 Criterion A: Persistent deficits in social communication and social "
    "interaction across multiple contexts, manifested by all three of: (1) deficits "
    "in social-emotional reciprocity — abnormal social approach, failure of normal "
    "back-and-forth conversation, reduced sharing of interests or emotions; "
    "(2) deficits in nonverbal communicative behaviors — poorly integrated verbal "
    "and nonverbal communication, abnormalities in eye contact and body language, "
    "lack of facial expressions and gestures; (3) deficits in developing, maintaining "
    "and understanding relationships — difficulty adjusting behavior to suit different "
    "social contexts, difficulty in sharing imaginative play, absence of interest in peers.",

    "DSM-5 Criterion B: Restricted, repetitive patterns of behavior, interests, or "
    "activities, manifested by at least two of: (1) stereotyped or repetitive motor "
    "movements, use of objects, or speech such as simple motor stereotypies, lining up "
    "toys, flipping objects, echolalia, idiosyncratic phrases; (2) insistence on sameness, "
    "inflexible adherence to routines, ritualized patterns of verbal or nonverbal behavior "
    "such as extreme distress at small changes, difficulty with transitions, rigid thinking; "
    "(3) highly restricted, fixated interests that are abnormal in intensity or focus; "
    "(4) hyper or hypo reactivity to sensory input or unusual interest in sensory aspects "
    "of the environment such as apparent indifference to pain or temperature, adverse "
    "responses to specific sounds or textures, excessive smelling or touching of objects.",

    "DSM-5 Criterion C: Symptoms must be present in the early developmental period "
    "though they may not fully manifest until social demands exceed limited capacities, "
    "or they may be masked by learned strategies later in life. "
    "Criterion D: Symptoms cause clinically significant impairment in social, occupational, "
    "or other important areas of current functioning. "
    "Criterion E: These disturbances are not better explained by intellectual disability "
    "or global developmental delay. DSM-5 severity levels are: Level 1 'Requiring Support', "
    "Level 2 'Requiring Substantial Support', Level 3 'Requiring Very Substantial Support'.",

    "DSM-5 ASD Severity Level 1 (Mild/Requiring Support): Without supports in place, "
    "deficits in social communication cause noticeable impairments. The person has "
    "difficulty initiating social interactions and demonstrates clear examples of "
    "atypical or unsuccessful responses to social overtures. May appear to have "
    "decreased interest in social interactions. Inflexibility of behavior causes "
    "significant interference in one or more contexts. Difficulty switching between "
    "activities. Problems of organization and planning hamper independence.",

    "DSM-5 ASD Severity Level 2 (Moderate/Requiring Substantial Support): Marked "
    "deficits in verbal and nonverbal social communication skills. Social impairments "
    "apparent even with supports in place. Limited initiation of social interactions "
    "and reduced or abnormal responses to social overtures from others. "
    "Inflexibility of behavior, difficulty coping with change, or other "
    "restricted/repetitive behaviors appear frequently enough to be obvious to the "
    "casual observer and interfere with functioning in a variety of contexts.",

    "DSM-5 ASD Severity Level 3 (Severe/Requiring Very Substantial Support): "
    "Severe deficits in verbal and nonverbal social communication skills cause "
    "severe impairments in functioning. Very limited initiation of social interactions "
    "and minimal response to social overtures from others. Inflexibility of behavior, "
    "extreme difficulty coping with change, or other restricted/repetitive behaviors "
    "markedly interfere with functioning in all spheres. Great distress or difficulty "
    "changing focus or action.",

    # ── SECTION 2: LEO KANNER — ORIGINAL 1943 CLINICAL DESCRIPTION ───────────

    "Leo Kanner (1943) was the first to describe autism as a distinct clinical syndrome "
    "at Johns Hopkins Hospital. Based on 11 children, he identified two primary features: "
    "(1) 'autistic aloneness' — an inability to relate to people and situations in an "
    "ordinary way from the earliest stages of life, and (2) 'an anxiously obsessive desire "
    "for the maintenance of sameness' — distress when routines are altered even slightly. "
    "He noted the children were mesmerized by objects but indifferent to people, had "
    "feeding difficulties in infancy, reacted fearfully to loud sounds, and preferred "
    "rigid repetitive routine over any novelty. Kanner concluded this was a "
    "neurodevelopmental disorder: 'these children have come into the world with an innate "
    "inability to form the usual, biologically provided contact with people.'",

    "Kanner's original 1943 observations included: (1) lack of communicative speech — "
    "some children were mute, others spoke but not to communicate; (2) echolalia and "
    "pronoun reversal — children repeated phrases heard elsewhere without communicative "
    "intent; (3) excellent rote memory — children could recite lists, poems, and "
    "sequences verbatim; (4) difficulty understanding abstract concepts; "
    "(5) stereotyped behaviors and lack of imaginative play; (6) 'autistic aloneness' "
    "— unawareness of other people. These children showed symptoms since infancy and "
    "had normal physical developmental histories. The catastrophic reactions to change "
    "resembled infantile rage: screaming, weeping, thrashing of arms and legs.",

    # ── SECTION 3: SIMON BARON-COHEN — THEORY OF MIND & MINDBLINDNESS ────────

    "Simon Baron-Cohen (Cambridge University) proposed the Theory of Mind (ToM) deficit "
    "hypothesis for autism. In his 1985 Sally-Anne false-belief task study with Frith and "
    "Leslie, children with autism failed to attribute false beliefs to others — they "
    "said Sally would look where the marble actually was, not where she had left it. "
    "This demonstrated that children with autism have difficulty understanding that "
    "others hold mental states different from reality. Baron-Cohen termed this "
    "'mindblindness' (1995): the inability to intuit what others are thinking, "
    "perceiving, intending, or believing. Typical humans mindread effortlessly and "
    "automatically; autistic children often cannot. This explains social and "
    "communicative challenges — the child cannot predict others' behavior from their "
    "mental states.",

    "Baron-Cohen's mindblindness theory explains why autistic children struggle with: "
    "taking turns in conversation (cannot model listener's knowledge state), "
    "understanding that pointing communicates interest to another person (requires ToM), "
    "responding to social bids (cannot interpret communicative intent), "
    "pretend play (requires representing false states), deception and white lies, "
    "understanding metaphors and sarcasm, and adjusting speech to the listener's "
    "knowledge level. Baron-Cohen also proposed the Empathizing-Systemizing (E-S) "
    "theory: autistic individuals have a stronger drive to systematize (analyze patterns, "
    "rules, and systems) than to empathize. This explains special interests in highly "
    "rule-based domains such as trains, timetables, mathematics, and computers.",

    "Baron-Cohen's Autism-Spectrum Quotient (AQ) and the Empathy Quotient (EQ) are "
    "widely used self-report screening tools. The AQ measures autistic traits in "
    "adults with normal intelligence across five domains: social skills, attention "
    "switching, attention to detail, communication, and imagination. A score of 26 "
    "or above suggests clinically significant autistic traits. Baron-Cohen's 'extreme "
    "male brain' theory (2002) proposes that autism represents an extreme of the "
    "male cognitive profile: high systemizing, low empathizing. This explains the "
    "higher prevalence in males (approximately 4:1 male-to-female ratio) though "
    "females are increasingly recognized as underdiagnosed due to masking.",

    # ── SECTION 4: UTA FRITH — CENTRAL COHERENCE & COGNITIVE THEORIES ────────

    "Uta Frith (UCL) proposed the Weak Central Coherence (WCC) theory of autism. "
    "Typically developing individuals process information by integrating details into "
    "a coherent whole (global processing). Autistic individuals tend to process "
    "information in parts — focused on local details rather than the global gestalt. "
    "This explains superior performance on the Embedded Figures Test (finding hidden "
    "shapes in complex patterns) and Block Design tasks, but difficulty understanding "
    "context-dependent meaning, facial expressions as wholes, and the 'gist' of stories. "
    "WCC also explains excellent rote memory for details, special talents in music "
    "and art (detail-focused), and hyperlexia (reading words without comprehension).",

    "Frith and colleagues also developed the Executive Function (EF) deficit theory "
    "of autism. EF includes planning, cognitive flexibility, working memory, inhibition, "
    "and monitoring. EF deficits in autism explain: difficulty shifting between tasks "
    "(rigid adherence to routines), perseveration on topics or activities, poor "
    "planning ahead, difficulty inhibiting inappropriate responses, and trouble "
    "self-monitoring behavior in social situations. EF deficits, together with "
    "ToM deficits and WCC, form the three major cognitive theories that explain "
    "the behavioral profile of autism spectrum disorder.",

    # ── SECTION 5: TEMPLE GRANDIN — SENSORY & VISUAL THINKING PERSPECTIVE ────

    "Temple Grandin (Colorado State University), herself autistic, describes sensory "
    "hypersensitivity as one of the most disabling aspects of autism. In her words: "
    "'sensory issues are a serious problem — they make it impossible to operate in the "
    "environment where you're supposed to be social.' Grandin describes thinking in "
    "pictures rather than words — all thoughts are photorealistic images, like a video "
    "library. Abstract concepts are linked to specific visual memories. This visual "
    "thinking style is common in many autistic individuals and explains why visual "
    "supports (picture schedules, social stories, PECS cards) are so effective.",

    "Temple Grandin documented that autistic children often prefer proximal sensory "
    "stimulation (touching, tasting, smelling) over distal stimulation (hearing, seeing). "
    "She invented the 'squeeze machine' (hug box) — a device providing controlled deep "
    "pressure stimulation — to calm her oversensitive nervous system. Deep pressure "
    "has a calming effect because it activates the parasympathetic nervous system. "
    "Grandin describes how incoming auditory and tactile stimulation overwhelmed her, "
    "causing self-imposed sensory restriction (withdrawal). She warns that forcing "
    "sensory exposure without the child's control increases distress rather than "
    "desensitization. Effective sensory therapy always gives the child control over "
    "the intensity and duration of stimulation.",

    "Temple Grandin's key clinical observations for parents and educators: "
    "(1) Do not let autistic children fixate on only one thing — gently expand interests; "
    "(2) Build on the child's strengths — visual thinking, pattern recognition, "
    "attention to detail can become vocational assets; "
    "(3) Sensory issues must be addressed before academic or social learning can occur — "
    "an overwhelmed nervous system cannot learn; "
    "(4) Structure, predictability, and visual cues reduce anxiety dramatically; "
    "(5) Early speech therapy is critical — a non-verbal child at age 3 may speak by age 5 "
    "with intensive intervention; "
    "(6) Avoid abstract language — give concrete, specific instructions; "
    "(7) Children on the spectrum often have uneven skills — severe deficits alongside "
    "remarkable abilities in other areas.",

    # ── SECTION 6: JEAN AYRES — SENSORY INTEGRATION THEORY ──────────────────

    "Jean Ayres (occupational therapist, 1970s) developed Sensory Integration (SI) theory. "
    "She proposed that some children's atypical behavior, learning problems, and physical "
    "clumsiness stem from the brain's inability to process and integrate sensory "
    "information from the body and environment effectively. The vestibular system "
    "(inner ear — movement and balance), proprioceptive system (muscles and joints — "
    "body position), and tactile system (touch) are the three primary systems targeted "
    "in SI therapy. Dysfunction causes: tactile defensiveness, gravitational insecurity, "
    "vestibular hypo/hypersensitivity, poor bilateral coordination, and dyspraxia "
    "(difficulty planning and executing unfamiliar motor sequences).",

    "Sensory Integration dysfunction in autism manifests as: (1) tactile defensiveness — "
    "extreme sensitivity to light touch, avoidance of certain textures in clothing and food, "
    "distress when hair is brushed or teeth cleaned; (2) auditory hypersensitivity — "
    "covering ears for ordinary sounds (vacuum cleaners, hand dryers, crowd noise), "
    "distress at unexpected sounds; (3) vestibular seeking — constant rocking, spinning, "
    "jumping to obtain vestibular input the brain craves; (4) proprioceptive seeking — "
    "crashing into furniture, chewing on objects, pressing hard with pencils, seeking "
    "deep pressure; (5) visual sensitivity — distress at fluorescent lights, preference "
    "for dim environments; (6) olfactory hypersensitivity — gagging at mild smells, "
    "refusing foods by smell before tasting. Research shows 42-95% of autistic children "
    "have significant sensory processing differences (Tomchek and Dunn, 2007).",

    "A sensory diet (Jean Ayres / OT concept) is a personalized schedule of sensory "
    "activities throughout the day that keeps the child's nervous system regulated. "
    "It includes: proprioceptive activities (heavy work — carrying books, pushing/pulling, "
    "climbing), vestibular activities (swinging, bouncing, rocking), deep pressure "
    "(weighted blankets, compression clothing, bear hugs), oral sensory input (chewing "
    "crunchy foods, using chewy tools), and calming activities (dim lighting, quiet "
    "spaces, slow rhythmic movement). Sensory diets should be implemented every "
    "90-120 minutes throughout the day. They are prescribed by occupational therapists "
    "and must be individualized to the child's specific sensory profile.",

    # ── SECTION 7: ASSESSMENT TOOLS — CLINICAL STANDARDS ────────────────────

    "ADOS-2 (Autism Diagnostic Observation Schedule, Second Edition): The gold standard "
    "observational assessment for autism. It is a semi-structured, standardized assessment "
    "of communication, social interaction, play, and restricted/repetitive behaviors. "
    "Administered by a trained clinician in a 40-60 minute session. Consists of 5 modules "
    "selected based on the child's expressive language level: Module 1 (pre-verbal/single "
    "words), Module 2 (phrase speech), Module 3 (fluent speech, child/adolescent), "
    "Module 4 (fluent speech, adults). Sensitivity 87%, specificity 75%. ADOS-2 scores "
    "can be mapped directly onto DSM-5 diagnostic criteria. It is administered by "
    "psychologists, psychiatrists, or specially trained speech-language pathologists.",

    "ADI-R (Autism Diagnostic Interview — Revised): A structured caregiver interview "
    "that is the complementary gold standard to ADOS-2. It is a comprehensive interview "
    "covering the child's developmental history and current behavior across three domains: "
    "(1) qualitative abnormalities in reciprocal social interaction, "
    "(2) qualitative abnormalities in communication, "
    "(3) restricted, repetitive, and stereotyped patterns of behavior. "
    "Contains 93 items and takes 1.5-2.5 hours. Requires training. Sensitivity 77%, "
    "specificity 68%. Together, ADOS-2 and ADI-R form the diagnostic gold standard used "
    "in research and specialist clinical settings worldwide.",

    "CARS-2 (Childhood Autism Rating Scale, Second Edition): A 15-item clinician rating "
    "scale completed using multiple inputs — parent report, teacher report, records review, "
    "and direct observation. Assesses: relating to people, imitation, emotional response, "
    "body use, object use, adaptation to change, visual response, listening response, "
    "taste/smell/touch response and use, fear/nervousness, verbal communication, "
    "nonverbal communication, activity level, level and consistency of intellectual "
    "response, and general impressions. Sensitivity 89%, specificity 79% — the highest "
    "of the major tools. Total score: 15-29.5 (non-autistic), 30-36.5 (mild-moderate "
    "autism), 37-60 (severe autism). Widely used because it requires less training "
    "than ADOS-2 and ADI-R.",

    "M-CHAT-R/F (Modified Checklist for Autism in Toddlers, Revised with Follow-Up): "
    "The most commonly used screening tool for children 16-30 months old. "
    "It is a 20-item parent questionnaire followed by a structured follow-up interview "
    "for screen-positive cases. Critical items include: (1) Does your child point to "
    "show you something interesting? (2) Does your child look at your face to check "
    "your reaction when faced with unfamiliar situations? (3) Does your child bring "
    "objects to show you? (4) Does your child look where you are pointing? "
    "(5) Does your child pretend (e.g., feed a doll)? Failure on 3 or more items "
    "warrants immediate referral for diagnostic evaluation. ",

    "SRS-2 (Social Responsiveness Scale, Second Edition): A 65-item rating scale "
    "completed by parents or teachers in 15-20 minutes. Measures the severity of "
    "autism spectrum symptoms in naturalistic social settings across five subscales: "
    "social awareness, social cognition, social communication, social motivation, "
    "and restricted interests and repetitive behavior. Scores are continuous — "
    "SRS-2 provides a dimensional measure of autistic traits rather than a binary "
    "diagnosis. Especially useful for measuring treatment progress over time and "
    "for population-level research. T-scores: 59 or below (within normal limits), "
    "60-65 (mild), 66-75 (moderate), 76+ (severe).",

    "SCQ (Social Communication Questionnaire): A 40-item parent questionnaire used "
    "as an initial screening instrument derived from the ADI-R. Takes 10 minutes to "
    "complete. Two forms: Lifetime (ages 4+) and Current (any age). A score of 15 or "
    "above warrants referral for comprehensive diagnostic evaluation. It screens "
    "effectively across three domains: communication, social interaction, and "
    "restricted/repetitive behaviors. Less comprehensive than ADOS-2 or ADI-R but "
    "useful as a low-cost, rapid first-stage screen in community settings.",

    # ── SECTION 8: EARLY WARNING SIGNS BY AGE ────────────────────────────────

    "Red flags for autism by 12 months: (1) no babbling, pointing, or other gestures; "
    "(2) no response to own name when called; (3) no back-and-forth sharing of sounds, "
    "smiles, or other facial expressions; (4) no interest in other children; "
    "(5) no joint attention — child does not follow adult's gaze or pointing; "
    "(6) lack of eye contact or difficulty maintaining it; "
    "(7) unusual sensory behaviors — fascination with lights, spinning objects, "
    "or adverse reactions to sounds or textures. "
    "Immediate referral is indicated if a child loses any previously acquired language "
    "or social skills at any age (developmental regression).",

    "Red flags for autism by 24 months: (1) no two-word meaningful phrases (not "
    "including imitating or repeating); (2) no single words by 16 months; "
    "(3) does not point to direct others' attention or show objects of interest; "
    "(4) does not follow a point — when adult points to an object, child does not "
    "look in that direction; (5) little interest in other children or peers; "
    "(6) does not engage in pretend or make-believe play; (7) repetitive use of "
    "objects (lines up toys, spins wheels, flicks objects); "
    "(8) unusual attachment to specific objects; "
    "(9) marked sensitivity to sounds, textures, lights, or tastes.",

    "Red flags for autism by 36 months and older: (1) difficulty joining group play "
    "or maintaining friendships; (2) inability to take turns in games or conversation; "
    "(3) does not understand basic social rules (sharing, greetings, personal space); "
    "(4) literal interpretation of language — does not understand jokes, metaphors, "
    "or sarcasm; (5) highly unusual or intense preoccupations with specific topics; "
    "(6) insistence on very rigid routines with extreme distress at minor changes; "
    "(7) echolalia — repeating phrases from TV, books, or others in context or out "
    "of context; (8) unusual vocal patterns — monotone, sing-song, or very formal speech; "
    "(9) difficulty with perspective-taking — cannot explain why another person feels sad.",

    # ── SECTION 9: SOCIAL INTERACTION INDICATORS ─────────────────────────────

    "Social interaction deficits in autism across developmental levels: "
    "Infants may fail to anticipate being picked up, may not reach up to caregiver, "
    "may resist cuddling, may not orient to faces, and may show reduced social smile. "
    "Toddlers show little interest in other children, prefer solitary play, do not "
    "imitate others' actions spontaneously, and do not show objects to share experience "
    "(declarative pointing absent). Preschoolers may approach others but in atypical "
    "ways — may talk at rather than with others, may not understand the concept of "
    "friendship, and may be unaware of others' emotions and reactions to their behavior.",

    "Joint attention is one of the earliest and most reliable indicators of autism risk. "
    "It involves coordinating attention with another person about an object or event. "
    "There are two types: (1) imperative joint attention — requesting (pointing to get "
    "something desired); (2) declarative joint attention — sharing interest (pointing "
    "to show something interesting to another, checking the other person's gaze). "
    "Declarative joint attention is particularly impaired in autism and is absent or "
    "significantly delayed. A child who does not point to share interest in objects "
    "by 12 months is at high risk for autism. Joint attention is foundational for "
    "language development, social learning, and theory of mind.",

    "Social motivation theory (Chevallier, 2012): autistic individuals may have reduced "
    "intrinsic motivation to seek social interaction because social rewards (eye contact, "
    "smiles, praise) are less neurologically rewarding for them. The social brain circuitry "
    "— amygdala, medial prefrontal cortex, superior temporal sulcus, fusiform face area — "
    "may be atypically activated by social stimuli. This is not willful avoidance but a "
    "neurobiological difference in social reward processing. Implications: interventions "
    "should make social interaction intrinsically motivating by pairing it with "
    "the child's preferred activities, interests, and sensory experiences.",

    # ── SECTION 10: COMMUNICATION PROFILES ───────────────────────────────────

    "Communication in autism spans a wide spectrum: approximately 25-30% of autistic "
    "individuals remain minimally verbal or non-verbal. Among verbal children, common "
    "patterns include: (1) echolalia — immediate (repeating what was just said) or "
    "delayed (scripted phrases from TV, books, prior conversations used out of context); "
    "(2) pronoun reversal — saying 'you want juice' instead of 'I want juice'; "
    "(3) hyperlexia — ability to read written words at an early age without comprehension; "
    "(4) pedantic or formal speech — overly precise, adult-sounding vocabulary; "
    "(5) monotone or unusual prosody — flat, sing-song, or robotic speech; "
    "(6) literal interpretation — taking idioms literally ('it's raining cats and dogs' "
    "causes visual imagery of falling animals); (7) difficulty with narrative — "
    "cannot tell a coherent story with beginning, middle, and end.",

    "Pragmatic language (the social use of language) is consistently impaired in autism "
    "regardless of vocabulary or grammatical ability. Pragmatic deficits include: "
    "not adjusting speech to the listener's knowledge level (giving too much or too "
    "little context), not taking turns in conversation, interrupting or talking over "
    "others, not maintaining the topic of conversation, not repairing communication "
    "breakdowns when misunderstood, not using appropriate greetings or farewells, "
    "not reading nonverbal signals (facial expressions, tone of voice, body language), "
    "and not understanding implication or what is left unsaid. "
    "A child may have a large vocabulary but be unable to maintain a two-minute "
    "back-and-forth conversation on a topic chosen by the other person.",

    "Augmentative and Alternative Communication (AAC) for non-verbal or minimally verbal "
    "autistic children: research strongly supports early introduction of AAC — it does "
    "not reduce motivation to speak and may actually accelerate speech development. "
    "AAC options include: (1) PECS (Picture Exchange Communication System) — child "
    "physically hands picture cards to communicate; (2) speech-generating devices "
    "(SGDs) such as Proloquo2Go, TouchChat — high-tech apps on tablets; "
    "(3) core vocabulary boards — laminated boards with most frequently used words; "
    "(4) sign language — partial use alongside speech; "
    "(5) visual scene displays. AAC must be available 24/7 — it is the child's voice. "
    "Removing AAC as a consequence is never acceptable.",

    # ── SECTION 11: REPETITIVE BEHAVIORS & RESTRICTED INTERESTS ──────────────

    "Repetitive behaviors in autism are categorized into two types: "
    "(1) Lower-order: simple motor stereotypies (hand flapping, rocking, spinning, "
    "toe walking, mouthing objects, finger flicking, vocalizations like humming or "
    "squealing). These are primarily sensory-regulatory — the child is self-stimulating "
    "or self-soothing. They increase when the child is excited, anxious, or "
    "understimulated. (2) Higher-order: insistence on sameness, rituals, compulsions, "
    "and circumscribed interests. These involve cognitive rigidity and are more related "
    "to anxiety and difficulty with uncertainty. Both types are meaningful behaviors "
    "that serve functions — suppressing them without addressing the underlying need "
    "causes distress.",

    "Restricted and repetitive behaviors (RRBs) serve important functions for autistic "
    "children: (1) Sensory regulation — stimming provides sensory input that regulates "
    "arousal levels; (2) Anxiety management — rigid routines reduce unpredictability "
    "and lower anxiety; (3) Communication — repetitive behavior may signal that the "
    "child's needs are not being met; (4) Pleasure and intrinsic motivation — some "
    "RRBs are simply enjoyable. Research (Liss et al., 2001) shows that insistence on "
    "sameness is more strongly associated with anxiety, while sensory-motor repetitions "
    "are associated with sensory processing differences. Intervention should identify "
    "the function of each RRB before attempting to modify it.",

    "Circumscribed special interests in autism: intense, focused preoccupation with "
    "specific topics that is abnormal in intensity or focus. Common topics include "
    "transportation (trains, planes, buses), animals, maps, numbers, calendars, weather, "
    "specific TV shows, fictional characters, science topics, and music. "
    "These interests are often a strength rather than a deficit — they represent deep "
    "expertise and can become vocational assets. Research by Mottron (2011) proposes "
    "that autistic interests represent 'enhanced perceptual functioning' — superior "
    "processing of details in a domain of expertise. Interventions should channel "
    "special interests into social connection, academic engagement, and skill development "
    "rather than suppressing them.",

    # ── SECTION 12: ACTIVITY-SPECIFIC CLINICAL INDICATORS ────────────────────

    # Eating
    "Clinical indicators during eating activities in autism: (1) extreme food selectivity "
    "(neophobia) — accepting fewer than 20 foods, often restricted to specific colors, "
    "textures, brands, or presentations; (2) gagging or vomiting at novel foods; "
    "(3) distress if foods touch each other on the plate; (4) insistence on specific "
    "utensils, plates, or preparation methods; (5) inability to sit at the table for "
    "the duration of a meal; (6) mealtime meltdowns at least weekly; "
    "(7) sensory-based rejection — refusing foods by smell before tasting, "
    "spitting out foods of certain textures; (8) rituals around food — eating in exact "
    "order, arranging food before eating; (9) pica — eating non-food items such as "
    "dirt, paper, or paint (requires immediate medical evaluation).",

    "Feeding difficulties in autism are primarily sensory-driven. The oral sensory "
    "system is hypersensitive — certain textures (mushy, crunchy, slimy), temperatures, "
    "or flavors trigger a gag or avoidance response disproportionate to the stimulus. "
    "Visual sensitivity also plays a role — foods of certain colors or appearances "
    "are rejected before tasting. A 'food chaining' approach (building tolerance from "
    "accepted foods to similar-but-new foods) is evidence-based. Feeding therapy with "
    "an occupational therapist and speech-language pathologist (feeding specialist) "
    "is indicated when the diet is so restricted it risks nutritional deficiency "
    "or significantly impacts family functioning.",

    # Drinking
    "Clinical indicators during drinking activities in autism: (1) insistence on a "
    "specific cup, straw, or sippy cup — distress if it is unavailable; "
    "(2) refusing drinks by smell before tasting; (3) preference for drinks at "
    "specific temperatures (only very cold, or only room temperature); "
    "(4) difficulty transitioning from bottle to cup (may persist past age 3-4); "
    "(5) spilling frequently due to poor cup management and motor coordination; "
    "(6) drinking in ritualistic ways — only a specific number of sips, only "
    "in a specific location; (7) limited variety — may accept only one or two beverages; "
    "(8) seeking sensory input through drinking — blowing bubbles in drinks, "
    "swishing liquid in mouth.",

    # Writing and Drawing
    "Clinical indicators during writing and drawing activities in autism: "
    "(1) atypical pencil grip — fist grip, four-finger grasp, or holding pencil "
    "at the very tip or far end; (2) excessive pressure — pressing so hard the "
    "pencil tears the paper; (3) hypotonia (low muscle tone) — difficulty maintaining "
    "seated posture or holding a pencil at all; (4) dysgraphia-like features — "
    "poorly formed, inconsistently sized letters with no regard for lines; "
    "(5) repetitive drawing — drawing the same image, shape, or pattern repeatedly "
    "with high precision; (6) resistance to copying models or following instructions "
    "for drawing; (7) hyperlexia — writing out letters and words accurately but "
    "without meaningful use; (8) savant-level drawing ability in some cases — "
    "photographically precise drawings from memory.",

    # Playing
    "Clinical indicators during play activities in autism: "
    "(1) functional play absent or delayed — child does not use toys according to "
    "their intended purpose (e.g., spins car wheels rather than driving car); "
    "(2) symbolic/pretend play absent or delayed — child does not pretend to feed "
    "a doll or use a block as a phone; (3) repetitive, stereotyped play — "
    "same sequence of actions repeated identically each time; "
    "(4) lining up or sorting objects by color, size, or type rather than playing "
    "with them functionally; (5) solitary play preference — actively avoids or "
    "ignores peer play; (6) parallel play without interaction — plays near peers "
    "but not with them; (7) extreme distress if play sequence is interrupted or "
    "objects are moved; (8) rigid adherence to self-invented rules that cannot "
    "be changed; (9) fascination with parts of objects (wheels, hinges, lights) "
    "rather than the object as a whole.",

    # Communicating
    "Clinical indicators during communication activities in autism: "
    "(1) does not initiate communication spontaneously for social purposes — "
    "only communicates to request desired objects or to stop unwanted situations; "
    "(2) echolalia — immediate repetition of others' speech or delayed scripted "
    "phrases from media; (3) does not respond to social bids — ignores greetings, "
    "questions, or bids for attention; (4) monotone or unusual prosody; "
    "(5) does not adjust communication to listener — gives the same information "
    "regardless of what the listener already knows; (6) does not repair communication "
    "breakdowns — continues as if understood even when listener signals confusion; "
    "(7) inability to maintain a reciprocal conversation on a topic chosen by "
    "the other person for more than 2-3 exchanges; (8) talks at length about "
    "special interests without noticing listener's disinterest.",

    # Social Interaction
    "Clinical indicators during social interaction activities in autism: "
    "(1) does not greet familiar people spontaneously — must be prompted; "
    "(2) unusual eye contact — may avoid it entirely, or stare intensely; "
    "(3) does not share positive emotions with others — does not look to "
    "caregiver's face to share excitement or seek reassurance in new situations; "
    "(4) difficulty understanding social hierarchy — treats all adults the same "
    "regardless of authority role; (5) difficulty with reciprocity — takes "
    "objects from peers without asking, does not offer objects to share; "
    "(6) does not understand the concept of friendship — may call anyone "
    "they interact with a 'friend'; (7) misreads facial expressions and tone — "
    "does not recognize anger or sadness on faces; (8) naive and literal "
    "— easily manipulated by peers due to inability to detect deception.",

    # ── SECTION 13: CO-OCCURRING CONDITIONS ──────────────────────────────────

    "Co-occurring conditions in autism are the rule rather than the exception. "
    "Research shows: 70% of autistic individuals have at least one co-occurring "
    "mental health condition, 41% have two or more. Common co-occurring conditions: "
    "(1) ADHD — 50-70% of autistic children also meet criteria for ADHD "
    "(attention difficulties, hyperactivity, impulsivity); "
    "(2) Anxiety disorders — 40-60% (social anxiety, generalized anxiety, "
    "specific phobias, OCD-like presentations); "
    "(3) Intellectual disability — approximately 31% (IQ below 70); "
    "(4) Epilepsy — 20-30% (higher in severe presentations); "
    "(5) Sleep disorders — 50-80% (difficulty falling asleep, night waking, "
    "early morning waking — often related to melatonin dysregulation); "
    "(6) Gastrointestinal problems — 46-84% (constipation, diarrhea, "
    "abdominal pain — often related to sensory and anxiety issues); "
    "(7) Depression — increasingly recognized in adolescents and adults.",

    "ADHD and autism co-occurrence: when both are present, the child shows "
    "inattention AND social communication deficits AND repetitive behaviors. "
    "The combination is more challenging than either alone. Stimulant medications "
    "used for ADHD may worsen anxiety, irritability, or tics in autistic children "
    "and must be used with caution and monitoring. Behavioral interventions must "
    "address both executive function deficits (ADHD) and social/sensory needs (autism). "
    "Parent and teacher ratings on ADHD scales may be inflated by autism-related "
    "behaviors that resemble inattention but have different causes "
    "(sensory distraction, language processing delay, task avoidance).",

    "Sleep problems in autism: 50-80% of autistic children have significant sleep "
    "difficulties. Causes include: anxiety, sensory sensitivities (light, sound, "
    "texture of bedding), melatonin dysregulation (studies show atypical melatonin "
    "secretion patterns), irregular circadian rhythms, and co-occurring ADHD. "
    "Sleep deprivation worsens all autism symptoms: increases irritability, reduces "
    "attention and learning, worsens emotional regulation, and increases repetitive "
    "behaviors. Evidence-based interventions: sleep hygiene protocols, weighted "
    "blankets, blackout curtains, white noise, consistent bedtime routine, "
    "melatonin supplementation (under paediatric guidance), and CBT-adapted "
    "for autism.",

    "Gastrointestinal (GI) problems in autism: 46-84% of autistic children experience "
    "GI symptoms — significantly higher than the general pediatric population. "
    "Common issues: chronic constipation (most common), diarrhea, abdominal pain, "
    "gastroesophageal reflux, and food selectivity-related nutritional deficiencies. "
    "GI discomfort may be expressed as increased challenging behavior, self-injurious "
    "behavior, aggression, or increased stimming (because the child cannot verbally "
    "communicate pain). GI symptoms should always be considered when unexplained "
    "behavioral changes occur. Dietary interventions (high fiber, probiotics) and "
    "medical management may improve both GI symptoms and associated behaviors.",

    # ── SECTION 14: EVIDENCE-BASED INTERVENTIONS ─────────────────────────────

    "Applied Behavior Analysis (ABA): the most extensively researched intervention "
    "for autism spectrum disorder. ABA applies behavioral principles to teach new "
    "skills and reduce challenging behaviors. Core principles: positive reinforcement "
    "(increasing desired behaviors by following them with rewarding consequences), "
    "prompting (providing assistance to produce a behavior) with systematic prompt "
    "fading, task analysis (breaking complex skills into small teachable steps), "
    "generalization training (practicing skills across settings, people, and materials), "
    "and data-based decision making. Comprehensive ABA programs for young children "
    "(20-40 hours/week, starting before age 5) show medium effects for intellectual "
    "functioning (SMD=0.51) and adaptive behavior (SMD=0.37) compared to treatment "
    "as usual (meta-analysis, 632 participants).",

    "Early Start Denver Model (ESDM): an evidence-based comprehensive early intervention "
    "for toddlers 12-48 months old with autism. Integrates ABA teaching strategies "
    "within an affectively rich, relationship-focused, play-based context. "
    "Developed by Sally Rogers and Geraldine Dawson. In the landmark RCT (Dawson et al., "
    "2010), toddlers receiving 15-20 hours/week of ESDM over 2 years showed "
    "significantly greater improvements in IQ, language, adaptive behavior, and "
    "autism symptoms compared to community treatment. ESDM improves outcomes because "
    "it targets the social motivation deficit directly — making social interaction "
    "joyful and intrinsically rewarding. Parents are trained as co-therapists to "
    "implement ESDM throughout all daily routines.",

    "PECS (Picture Exchange Communication System): a structured AAC program for "
    "non-verbal or minimally verbal autistic individuals. Developed by Bondy and Frost. "
    "Teaches functional communication in 6 phases: Phase 1 (exchange a picture for a "
    "desired item), Phase 2 (go to communication partner to exchange), Phase 3 "
    "(discriminate between pictures), Phase 4 (construct sentences — 'I want' + item), "
    "Phase 5 (respond to 'what do you want?'), Phase 6 (comment on the environment). "
    "Meta-analyses show PECS increases spontaneous communication and may accelerate "
    "verbal speech development. PECS should be used in all environments and should "
    "never be removed as a consequence.",

    "PRT (Pivotal Response Training): a naturalistic ABA intervention targeting "
    "'pivotal' areas of development — motivation, responsivity to multiple cues, "
    "self-management, and self-initiation — that when addressed produce widespread "
    "improvements across many non-targeted behaviors. Developed by Robert and Lynn "
    "Koegel. PRT uses natural reinforcers (activities the child chooses), child choice, "
    "turn-taking, and reinforcing attempts rather than only correct responses. "
    "Evidence supports PRT for improving language, social interaction, play, and "
    "reducing disruptive behavior. PRT is particularly effective because it "
    "increases motivation and addresses generalization naturally.",

    "Speech and Language Therapy (SLT) for autism: SLT targets functional communication "
    "across all modalities. Key areas of focus: (1) pre-linguistic skills — eye contact, "
    "joint attention, intentional communication, imitation; (2) expressive language — "
    "vocabulary, sentence structure, requesting, commenting; (3) receptive language — "
    "following instructions, understanding questions, comprehension; "
    "(4) pragmatics — conversation skills, topic maintenance, narrative; "
    "(5) AAC — introduction and training for non-verbal children; "
    "(6) social communication — understanding jokes, metaphors, perspective-taking; "
    "(7) feeding therapy — desensitization, chewing, swallowing. "
    "Frequency: 1-3 sessions per week for mild-moderate; 3-5 for severe. "
    "Parent coaching between sessions is essential for generalization.",

    "Occupational Therapy (OT) for autism addresses: (1) sensory processing — "
    "sensory diet, sensory integration therapy, desensitization; "
    "(2) fine motor skills — pencil grasp, handwriting, scissors, self-care tasks; "
    "(3) gross motor skills — balance, coordination, bilateral integration; "
    "(4) activities of daily living — dressing, feeding, grooming, toileting; "
    "(5) visual-motor integration — copying, tracing, spatial awareness; "
    "(6) play skills — expanding play repertoire, introducing new materials; "
    "(7) executive function — organization, sequencing, planning activities. "
    "OT uses Ayres Sensory Integration therapy, the Wilbarger Brushing Protocol "
    "for tactile defensiveness, and therapeutic listening programs. "
    "Frequency: 1-3 sessions per week. Home program is essential.",

    "Social Skills Groups: structured, facilitated group interventions for autistic "
    "children to practice social skills with peers. Evidence-based curricula include "
    "PEERS (Program for the Education and Enrichment of Relational Skills — UCLA), "
    "Social Thinking by Michelle Garcia Winner, and various school-based programs. "
    "Typical targets: greeting peers, joining ongoing play or conversation, "
    "maintaining back-and-forth conversation, reading facial expressions and body "
    "language, understanding friendship rules, dealing with teasing, and handling "
    "rejection. Small groups of 4-8 children with 1-2 adult facilitators. "
    "Weekly sessions with parent involvement components. Research supports "
    "social skills groups for improving social knowledge and motivation in "
    "Level 1 and 2 autism.",

    "Cognitive Behavioral Therapy (CBT) adapted for autism: evidence-based for "
    "anxiety and emotional regulation in autistic children with good verbal ability "
    "(IQ > 70, mental age 7+). Modifications for autism: visual tools (emotion "
    "thermometers, thought-feeling-behavior diagrams), concrete and literal language, "
    "visual schedules for sessions, focus on cognitive and somatic symptoms of anxiety "
    "rather than internal emotional states, explicit teaching of relaxation techniques, "
    "and involving parents as co-therapists. Randomized controlled trials show "
    "adapted CBT significantly reduces anxiety in autistic children compared to "
    "waitlist controls.",

    # ── SECTION 15: FAMILY AND PARENT GUIDANCE ───────────────────────────────

    "Parent-mediated interventions produce significant improvements in child outcomes "
    "in autism. The Hanen 'More Than Words' program (for parents of autistic children "
    "under 5) teaches parents to follow the child's lead, join into the child's "
    "activities, and create opportunities for communication throughout daily routines. "
    "RCTs show 'More Than Words' improves parental responsiveness and child "
    "communication. Greenspan's Floortime (DIR/Floortime) model similarly emphasizes "
    "following the child's emotional lead and building circles of communication. "
    "The key principle across all parent-mediated approaches: parental warmth, "
    "responsiveness, and following the child's lead are more important than "
    "specific techniques.",

    "Caregiver stress in autism: parents of autistic children report significantly "
    "higher stress than parents of typically developing children or children with "
    "other developmental disabilities. Sources of stress include: child's challenging "
    "behavior (aggression, self-injury, meltdowns), sleep deprivation, social isolation, "
    "financial burden of therapies, navigating complex service systems, grief associated "
    "with diagnosis, and impact on siblings. Evidence-based supports for parent "
    "wellbeing: parent support groups, respite care, individual counseling or CBT, "
    "mindfulness-based stress reduction (MBSR) programs adapted for autism parents, "
    "and sibling support programs. Addressing caregiver mental health is essential "
    "because caregiver wellbeing directly affects child outcomes.",

    "Visual supports are a cornerstone of autism intervention across severity levels. "
    "Types: (1) visual schedules — photos or pictures of daily routine steps posted "
    "at the child's eye level, reviewed before transitions; (2) first-then boards — "
    "'First: shoes, Then: iPad' — prepares child for expected sequence; "
    "(3) social stories (Carol Gray) — personalized short stories written from the "
    "child's perspective describing a social situation and expected responses; "
    "(4) emotion cards — visual representations of feelings to help child identify "
    "and express emotional states; (5) choice boards — 2-4 options with pictures "
    "to reduce communication demands and increase autonomy; "
    "(6) task completion strips — showing the number of steps and checking off each. "
    "Research consistently shows visual supports reduce anxiety, improve compliance, "
    "and increase independence across settings.",

    # ── SECTION 16: EDUCATOR AND SCHOOL CONSIDERATIONS ───────────────────────

    "Inclusive education for autistic children requires individualized supports. "
    "The IEP (Individualized Education Program) / EHCP (Education, Health and Care Plan) "
    "should include: present levels of performance, measurable annual goals across "
    "all impaired domains, specially designed instruction, related services (SLT, OT, "
    "behavioral support), accommodations and modifications, and transition planning. "
    "Key classroom accommodations: preferred seating (away from sensory triggers), "
    "advance warning of schedule changes, visual schedule posted in classroom, "
    "sensory breaks written into the day, extended time for assignments, "
    "reduced written output requirements, quiet testing environment, and "
    "designated calm-down space.",

    "Positive Behavior Support (PBS) in schools: a proactive, function-based approach "
    "to managing challenging behavior in autistic students. The ABC framework: "
    "Antecedent (what happens before the behavior) — Behavior (what the student does) "
    "— Consequence (what happens after). Functional Behavior Assessment (FBA) "
    "identifies the function of each challenging behavior: sensory regulation, "
    "escape from demands, attention, or access to tangibles. The Behavior Intervention "
    "Plan (BIP) addresses the function — replacing challenging behaviors with "
    "functionally equivalent appropriate alternatives, modifying antecedents, "
    "and changing consequences. Punishment-based approaches without FBA are "
    "ineffective and harmful for autistic students.",

    # ── SECTION 17: SCORING FRAMEWORK & SEVERITY INDICATORS ─────────────────

    "Autism scoring framework for assessment: "
    "Score 0.0-2.9 (Mild/Level 1): Child shows some atypical social-communicative "
    "behaviors but has functional language and basic social engagement. May struggle "
    "in unstructured social situations but can participate with support. Repetitive "
    "behaviors and restricted interests are present but do not significantly impair "
    "daily functioning. Would benefit from social skills group, SLT, and parent "
    "coaching. ",

    "Score 3.0-5.9 (Moderate/Level 2): Clear autism features affecting daily "
    "functioning across home, school, and community settings. Communication is "
    "functional but significantly impaired in pragmatics and social reciprocity. "
    "Repetitive behaviors and insistence on sameness cause noticeable interference. "
    "Sensory sensitivities impact participation in daily activities. Requires "
    "specialist multidisciplinary intervention: ABA or ESDM, SLT 2-3x/week, "
    "OT for sensory and motor needs, social skills groups. Assessment "
    "recommended every 2-3 months.",

    "Score 6.0-10.0 (Severe/Level 3): Significant impairments in social communication "
    "and behavior across all domains. May be minimally verbal or non-verbal. "
    "Daily functioning severely impacted. Repetitive behaviors and sensory needs "
    "dominate daily life and require intensive management. Co-occurring intellectual "
    "disability, epilepsy, or significant medical needs likely. Requires intensive "
    "multidisciplinary support: intensive ABA 30-40 hours/week, AAC, intensive OT, "
    "medical management of co-occurring conditions, 1:1 educational support. "
    "Assessment every 4-6 weeks.",

    "Dimension scoring guide — what each dimension measures: "
    "Social Interaction (0-10): quality of eye contact, joint attention, peer play, "
    "social bids, reciprocity. Communication (0-10): expressiveness, pragmatics, "
    "echolalia, clarity, and functional use. Repetitive Behaviors (0-10): "
    "frequency and impact of stereotypies, insistence on sameness, and "
    "restricted interests. Sensory Response (0-10): severity of hyper/hyposensitivity "
    "across sensory modalities. Daily Living Skills (0-10): independence in eating, "
    "dressing, hygiene, and community functioning. Emotional Regulation (0-10): "
    "frequency and intensity of meltdowns, frustration tolerance, and ability to "
    "self-soothe.",

    # ── SECTION 18: EMOTIONAL REGULATION & MELTDOWNS ─────────────────────────

    "Autistic meltdowns vs. tantrums: a meltdown is an involuntary response to "
    "overwhelming sensory, emotional, or cognitive input — not a deliberate behavior "
    "for manipulation or attention. During a meltdown the child cannot control "
    "their behavior and may scream, cry, hit, bite, bang their head, or run. "
    "Unlike tantrums, meltdowns: occur regardless of audience, do not stop when "
    "demands are given in, may escalate when adults attempt to control them, "
    "and are followed by exhaustion and shame. Recovery takes 20-60+ minutes. "
    "Triggers: sensory overload, unexpected change, transition, hunger, fatigue, "
    "communication failure, or cumulative stress build-up over the day. "
    "Prevention requires identifying and managing triggers proactively.",

    "The meltdown cycle has three phases: (1) Rumbling — early warning signs: "
    "increased stimming, becoming quieter or more agitated, physical tension, "
    "repetitive questioning, refusing requests. This is the optimal intervention "
    "point — a sensory break, preferred activity, or removal of the trigger can "
    "prevent escalation; (2) Rage — full meltdown — the child needs safety, not "
    "intervention. Remove dangerous objects, clear the space, keep a calm presence, "
    "do not issue demands, do not attempt to reason or discuss; "
    "(3) Recovery — the child is exhausted and often remorseful. This is not the "
    "time for consequences or debriefing. Provide quiet, comfort, and time to recover. "
    "Debrief calmly much later when the child is fully regulated.",

    # ── SECTION 19: EVIDENCE-BASED FACTS FOR AI SCORING ─────────────────────

    "Key research findings for autism assessment: "
    "(1) Prevalence: CDC 2023 data — 1 in 36 children in the US has autism (up from "
    "1 in 150 in 2000). Male:female ratio approximately 4:1, though females are "
    "significantly underdiagnosed. (2) Heritability: autism has a genetic component "
    "estimated at 64-91% from twin studies. If one child has autism, the sibling "
    "recurrence risk is 15-20%. (3) Optimal diagnosis age: ADOS-2 and experienced "
    "clinicians can reliably diagnose autism in children as young as 18-24 months. "
    "Average age of diagnosis in the US remains around 4 years despite earlier "
    "detection being possible and better for outcomes.",

    "Early intervention outcome research: children who receive intensive, evidence-based "
    "intervention before age 3 show the greatest improvement. Studies show IQ gains "
    "of 9-15 points in children receiving early intensive behavioral intervention "
    "(EIBI). Approximately 3-25% of autistic children (studies vary) achieve "
    "'optimal outcomes' — meeting criteria for ASD in childhood but not adulthood. "
    "These children typically received early, intensive intervention and had "
    "higher initial IQ and language levels. Even children who do not achieve "
    "optimal outcomes benefit significantly — gaining independence, communication, "
    "and quality of life. The 'wait and see' approach is not supported by evidence "
    "and results in worse outcomes.",

]


class RAGEngine:
    _instance    = None
    _collection  = None
    _embed_model = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        import chromadb
        from sentence_transformers import SentenceTransformer

        logger.info("Initialising RAG engine…")
        self._embed_model = SentenceTransformer('all-MiniLM-L6-v2')

        client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self._collection = client.get_or_create_collection(
            name='autism_knowledge',
            metadata={'hnsw:space': 'cosine'},
        )

        existing_count = self._collection.count()
        expected_count = len(AUTISM_KNOWLEDGE_BASE)

        # Force re-seed when the knowledge base size changes.
        # This avoids stale embeddings being used when the app was run previously.
        if existing_count != expected_count:
            logger.info(
                "ChromaDB re-indexing required (existing_count=%s expected_count=%s)…",
                existing_count, expected_count
            )
            try:
                client.delete_collection('autism_knowledge')
            except Exception:
                # If delete fails (e.g., collection missing), continue with get_or_create.
                pass

            self._collection = client.get_or_create_collection(
                name='autism_knowledge',
                metadata={'hnsw:space': 'cosine'},
            )

            logger.info("Seeding ChromaDB…")
            ids        = [f'doc_{i}' for i in range(expected_count)]
            embeddings = self._embed_model.encode(AUTISM_KNOWLEDGE_BASE).tolist()
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=AUTISM_KNOWLEDGE_BASE
            )
            logger.info(f"Added {expected_count} chunks to ChromaDB.")

    def add_custom_data(self, texts: list, ids: list = None):
        if ids is None:
            existing = self._collection.count()
            ids = [f'custom_{existing + i}' for i in range(len(texts))]
        embeddings = self._embed_model.encode(texts).tolist()
        self._collection.add(ids=ids, embeddings=embeddings, documents=texts)
        logger.info(f"Added {len(texts)} custom chunks to ChromaDB.")

    def retrieve(self, query: str, n_results: int = 5) -> list:
        embedding = self._embed_model.encode([query])[0].tolist()
        results   = self._collection.query(query_embeddings=[embedding], n_results=n_results)
        return results['documents'][0] if results['documents'] else []

    def analyze(self, transcription: str, child_info: dict, activity_type: str) -> dict:
        context_chunks = self.retrieve(f"{activity_type}: {transcription}", n_results=6)
        context        = '\n\n'.join(context_chunks)
        prompt         = self._build_prompt(transcription, child_info, activity_type, context)
        raw_response   = self._call_llm(prompt, transcription, activity_type, child_info.get('age'))
        return self._parse_response(raw_response)

    def _build_prompt(self, transcription, child_info, activity_type, context):
        return f"""You are an expert autism assessment AI assistant trained on DSM-5 criteria, 
ADOS-2/ADI-R/CARS clinical tools, and research by Baron-Cohen, Kanner, Grandin, and Frith.

## AUTISM KNOWLEDGE BASE (Retrieved Context)
{context}

## CHILD INFORMATION
- Name: {child_info.get('name', 'Unknown')}
- Age: {child_info.get('age', 'Unknown')} years
- Gender: {child_info.get('gender', 'Unknown')}

## ACTIVITY TYPE
{activity_type}

## PARENT'S DESCRIPTION
"{transcription}"

## YOUR TASK
Analyse the parent's description using DSM-5 criteria and the knowledge base above.
Respond ONLY with a valid JSON object (no markdown, no extra text):

{{
  "autism_score": <float 0.0-10.0, one decimal>,
  "severity_level": "<mild|moderate|severe>",
  "dimension_scores": {{
    "Social Interaction": <float 0.0-10.0>,
    "Communication": <float 0.0-10.0>,
    "Repetitive Behaviors": <float 0.0-10.0>,
    "Sensory Response": <float 0.0-10.0>,
    "Daily Living Skills": <float 0.0-10.0>,
    "Emotional Regulation": <float 0.0-10.0>
  }},
  "ai_analysis": "<2-4 sentence professional interpretation referencing specific observed behaviors>",
  "key_observations": ["<specific behavior 1>", "<specific behavior 2>", "<specific behavior 3>"],
  "immediate_recommendations": ["<clinical rec 1>", "<clinical rec 2>", "<clinical rec 3>"]
}}

Scoring guide:
- 0.0-2.9 = mild (Level 1 DSM-5: some atypical features, functional daily life)
- 3.0-5.9 = moderate (Level 2 DSM-5: clear impact on functioning, intervention required)
- 6.0-10.0 = severe (Level 3 DSM-5: significant impairments, intensive support needed)
Severity must match the score range exactly.
"""

    def _call_llm(self, prompt, transcription, activity_type, child_age):
        try:
            if settings.LLM_PROVIDER == 'anthropic':
                return self._call_anthropic(prompt)
            else:
                return self._call_openai(prompt)
        except Exception as e:
            logger.warning(f"LLM API failed ({settings.LLM_PROVIDER}): {str(e)}, falling back to mock analysis")
            return self._call_mock(transcription, activity_type, child_age)

    def _call_anthropic(self, prompt):
        import anthropic
        client  = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        message = client.messages.create(
            model='claude-opus-4-5',
            max_tokens=1024,
            messages=[{'role': 'user', 'content': prompt}],
        )
        return message.content[0].text

    def _call_openai(self, prompt):
        from openai import OpenAI
        client   = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model='gpt-4-turbo',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=1024,
            temperature=0.2,
        )
        return response.choices[0].message.content

    def _sanitize_transcription_for_mock(self, transcription: str) -> str:
        if not transcription:
            return ""
        text = transcription.strip()
        markers = [
            "## PARENT'S DESCRIPTION",
            "## PARENT'S DESCRIPTION".lower(),
            "PARENT'S DESCRIPTION",
            "AUTISM KNOWLEDGE BASE",
            "## AUTISM KNOWLEDGE BASE (Retrieved Context)",
        ]
        lower = text.lower()
        for m in markers:
            m_lower = m.lower()
            if m_lower in lower:
                idx = lower.find(m_lower)
                return text[idx + len(m):].strip()
        return text

    def _get_age_group(self, age):
        try:
            age = int(age)
        except:
            return "3-5"
        if age <= 2:   return "0-2"
        elif age <= 5: return "3-5"
        elif age <= 9: return "6-9"
        else:          return "10+"

    def _call_mock(self, transcription, activity_type, child_age):
        """Local analysis fallback when API is unavailable."""
        transcription = self._sanitize_transcription_for_mock(transcription)

        import re
        t = transcription.lower()

        def _negation_near_match(match_start: int, window: int = 10) -> bool:
            left_start = max(0, match_start - window)
            left = t[left_start:match_start]
            return bool(re.search(r"\b(not|no|never|without|can't|cannot|doesn't|do not|don't|didn't)\b\s*$", left))

        def any_regex(patterns: list) -> tuple:
            count = 0
            per_pattern = {}
            for p in patterns:
                m = re.search(p, t)
                if not m:
                    continue
                if _negation_near_match(m.start()):
                    per_pattern[p] = 0
                    continue
                count += 1
                per_pattern[p] = 1
            return count, per_pattern

        mild_evidence = [
            r"\b(enjoy|likes?)\b",
            r"\b(social|friend|peer)\b",
            r"\b(play)\b",
            r"\b(interact|interaction|interacting)\b",
            r"\b(talk|talking|speech|communicat(ion|es))\b",
            r"\b(normal|typical|typically)\b",
            r"\b(engag(e|es|ed|ing)|engagement)\b",
            r"\b(responsive)\b",
        ]

        moderate_evidence = [
            r"\b(difficulty|difficult|hard)\b",
            r"\b(struggle|struggles|challeng(e|ing))\b",
            r"\b(repetitive|stimming|stims|stereotyp)\b",
            r"\b(sensory|sensory processing)\b",
            r"\b(focus|focused|attention|hyperfocus)\b",
            r"\b(same (toy|game|activity|book|page|drawing))\b",
            r"\b(again and again|over and over|repeats? the same)\b",
            r"\b(gets? upset|becomes? upset|cries when)\b",
            r"\b(difficulty with change|doesn't like change|hates change)\b",
            r"\b(plays? alone|plays? by himself|by herself)\b",
            r"\b(focused for long periods|long periods)\b",
            r"\b(ignores? others|doesn't notice others)\b",
            r"\b(interest|special interest|restricted interest)\b",
            r"\b(delay|delayed)\b",
            r"\b(slow|slowness)\b",
            r"\b(routine|sameness|predictable|change(s)? upset|upset by changes)\b",
            r"\b(transit(ion)?s?|switching activities|transitions)\b",
        ]

        severe_evidence = [
            r"\b(no eye contact|avoids eye contact|limited eye contact)\b",
            r"\b(does(n't| not) respond to (his|her|their)? name|does(n't| not) respond to name)\b",
            r"\b(does(n't| not) follow (gaze|pointing|point))\b",
            r"\b(prefers? being alone|solitary play|parallel play)\b",
            r"\b(avoids? social interaction|struggles? to join (peer|peer(s)?) game(s)?)\b",
            r"\b(doesn't react to others|no interest in others)\b",
            r"\b(limited (gestures|pointing)|no pointing|does(n't| not) point)\b",
            r"\b(echolalia|echolalic|monotone speech)\b",
            r"\b(non-?verbal|nonverbal)\b",
            r"\b(refus(e|es|ing) (to )?(respond|answer|communicate|talk|interaction))\b",
            r"\b(noncompliant|uncooperative)\b",
            r"\b(hand flapp(ing|ed|es)?|rock(ing|ed|s)?|spinning|toe walking)\b",
            r"\b(lining up (toys|items)|lines up (toys|items))\b",
            r"\b(distressed by (small )?(changes|change in (routine|routine))|extreme distress)\b",
            r"\b(insists? on same routine|strict routine)\b",
            r"\b(must be the same|has to be the same)\b",
            r"\b(stays? in the same spot|sits? in the same spot)\b",
            r"\b(only plays? with one toy|single toy for long periods)\b",
            r"\b(refuses? new (toys|games|books|activities))\b",
            r"\b(avoid(s|ed|ing)? (textures|texture|sounds)|sensory aversion)\b",
            r"\b(covers? (his|her|their)? ears|cover(s|ed|ing)? ears)\b",
            r"\b(refuse(s|d|ing)? (food(s)? )?(by texture|by smell|smell))\b",
            r"\b(bright lights? distress|distress(ed|ing)? at bright lights?)\b",
            r"\b(extremely upset|very upset|intense distress)\b",
            r"\b(meltdown|tantrum)\b",
            r"\b(withdraw(n|n)?|shutdown)\b",
        ]

        mild_count,     _ = any_regex(mild_evidence)
        moderate_count, _ = any_regex(moderate_evidence)
        severe_count,   _ = any_regex(severe_evidence)

        evidence_total = mild_count + moderate_count + severe_count

        if evidence_total == 0:
            score = 2.0
        else:
            raw = (
                2.5
                + (moderate_count / evidence_total) * 4.2
                + (severe_count   / evidence_total) * 7.5
                + (mild_count     / evidence_total) * -1.0
            )
            score = raw

        score = max(0.0, min(10.0, float(score)))

        logger.info(
            "Mock scoring: mild=%s moderate=%s severe=%s total=%s score=%.2f",
            mild_count, moderate_count, severe_count, evidence_total, score
        )

        activity_key = (activity_type or "").strip().lower()
        if activity_key.startswith("play"):    activity_key = "playing"
        elif "read"   in activity_key:         activity_key = "reading"
        elif activity_key.startswith("draw"):  activity_key = "drawing"
        elif activity_key.startswith("eat"):   activity_key = "eating"
        elif activity_key.startswith("drink"): activity_key = "drinking"
        elif activity_key.startswith("write"): activity_key = "writing"
        elif "social" in activity_key:         activity_key = "social"

        weights = ACTIVITY_WEIGHTS.get(activity_key, {})

        def weighted(dim, base):
            return min(10, base * weights.get(dim, 1.0))

        dimension_scores = {
            "Social Interaction":   weighted("Social Interaction",   score * 1.1),
            "Communication":        weighted("Communication",        score * 1.0),
            "Repetitive Behaviors": weighted("Repetitive Behaviors", score * 1.0),
            "Sensory Response":     weighted("Sensory Response",     score * 1.0),
            "Daily Living Skills":  weighted("Daily Living Skills",  score * 0.85),
            "Emotional Regulation": weighted("Emotional Regulation", score * 1.05),
        }

        age_group  = self._get_age_group(child_age)
        age_weights = AGE_MULTIPLIERS.get(age_group, {})
        dimension_scores = {
            dim: min(10, val * age_weights.get(dim, 1.0))
            for dim, val in dimension_scores.items()
        }

        score = sum(dimension_scores.values()) / len(dimension_scores)
        severity_level = "mild" if score < 3 else ("moderate" if score < 6 else "severe")

        return json.dumps({
            "autism_score":   score,
            "severity_level": severity_level,
            "dimension_scores": dimension_scores,
            "ai_analysis": (
                f"Analysis performed using local assessment engine (API unavailable). "
                f"Score: {score:.1f}/10. Based on DSM-5 criteria and clinical indicators "
                f"extracted from the parent's description."
            ),
            "key_observations": [
                "Behavioral patterns identified through transcript analysis",
                "Activity-specific and age-adjusted dimension weighting applied",
                "Severity estimate derived from evidence-based keyword patterns"
            ],
            "immediate_recommendations": [
                "Schedule comprehensive professional assessment (ADOS-2 + ADI-R)",
                "Document all behavioral observations carefully with video if possible",
                "Share findings with a paediatric psychologist or developmental paediatrician"
            ]
        })

    def _parse_response(self, raw):
        try:
            clean = raw.strip()
            if clean.startswith('```'):
                clean = '\n'.join(clean.split('\n')[1:-1])
            result = json.loads(clean)
            score  = float(result.get('autism_score', 0))
            result['autism_score'] = max(0.0, min(10.0, score))
            if result['autism_score'] < 3:
                result['severity_level'] = 'mild'
            elif result['autism_score'] < 6:
                result['severity_level'] = 'moderate'
            else:
                result['severity_level'] = 'severe'
            return result
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                'autism_score': 0.0,
                'severity_level': 'mild',
                'dimension_scores': {
                    'Social Interaction': 0.0, 'Communication': 0.0,
                    'Repetitive Behaviors': 0.0, 'Sensory Response': 0.0,
                    'Daily Living Skills': 0.0, 'Emotional Regulation': 0.0,
                },
                'ai_analysis': 'Analysis could not be completed. Please try again.',
                'key_observations': [],
                'immediate_recommendations': [],
            }


def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribe audio using Whisper (faster_whisper).
    Fixes issues where transcription comes out in the wrong language by:
      - forcing English as default
      - logging metadata
      - rejecting clearly invalid/empty uploads
      - performing a single fallback retry if needed
    """
    import re
    from faster_whisper import WhisperModel

    if not audio_file_path:
        raise ValueError("audio_file_path is empty")

    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

    file_size = os.path.getsize(audio_file_path)
    logger.info("Transcribing audio_file_path=%s size_bytes=%s", audio_file_path, file_size)

    # Basic sanity check: very small/corrupted uploads often produce garbage text.
    # Threshold is 1 KB — short/compressed mobile recordings (AAC, OGG) can be <10 KB
    # so 10 KB was too aggressive and rejected valid short voice messages.
    if file_size < 1_000:  # 1 KB
        raise ValueError(f"Audio upload too small/corrupted (size_bytes={file_size})")

    # BUG FIX: use a None-sentinel module-level variable instead of the
    # fragile `global` + `if name not in globals()` pattern, which is
    # unreliable across Django dev-server auto-restarts.
    global _whisper_model_instance
    if _whisper_model_instance is None:
        whisper_model_size = getattr(settings, 'WHISPER_MODEL', 'base')
        logger.info("Loading Whisper model: %s", whisper_model_size)
        _whisper_model_instance = WhisperModel(
            model_size_or_path=whisper_model_size,
            compute_type="int8",
        )

    # 1) Primary attempt: force English.
    # faster_whisper supports language codes (e.g., "en").
    # BUG FIX: consume the generator into a list immediately —
    # faster_whisper.transcribe() returns a lazy generator that can only
    # be iterated once; converting to list avoids silent empty results if
    # the generator is accidentally iterated a second time.
    segments_gen, info = _whisper_model_instance.transcribe(
        audio_file_path,
        beam_size=5,
        language="en",
        vad_filter=True,
    )
    segments = list(segments_gen)

    text = " ".join(s.text for s in segments).strip()
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # 2) Fallback retry: if we got almost nothing, try without language forcing.
    # This avoids wrong-language garbage for normal audio while still handling edge cases.
    if len(text) < 3:
        logger.warning(
            "Transcription too short after forced-English attempt. Retrying without language forcing. "
            "file=%s detected_lang=%s",
            audio_file_path,
            getattr(info, "language", None),
        )

        segments2_gen, info2 = _whisper_model_instance.transcribe(
            audio_file_path,
            beam_size=5,
            language=None,
            vad_filter=True,
        )
        segments2 = list(segments2_gen)
        text = " ".join(s.text for s in segments2).strip()
        text = re.sub(r"\s+", " ", text)

    return text

