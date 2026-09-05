#!/usr/bin/env python3
"""
Publication Tag Classifier for Conscious Brain Lab
Audits all publications against titles, citations, abstracts, and methods.
Classifies into the 15 official CBL topics:
  Methods:
    - EEG
    - fMRI
    - MEG
    - Pupillometry
    - Pharmacology
    - Neural Decoding
  Topics:
    - Consciousness
    - Cognitive Control
    - Decision Making
    - Perception & Vision
    - Metacognition & Confidence
    - Hypnosis
    - Language & Semantics
    - Disorders of Consciousness
    - Cognitive Neuroscience
"""

import json
import re
import os

VALID_TOPICS = [
    "Cognitive Control",
    "Cognitive Neuroscience",
    "Consciousness",
    "Decision Making",
    "Disorders of Consciousness",
    "EEG",
    "fMRI",
    "Hypnosis",
    "Language & Semantics",
    "MEG",
    "Metacognition & Confidence",
    "Neural Decoding",
    "Perception & Vision",
    "Pharmacology",
    "Pupillometry"
]

def analyze_paper(pub):
    title = pub.get('title') or ''
    abstract = pub.get('abstract') or ''
    citation = pub.get('citation') or ''
    journal = pub.get('journal') or ''
    keywords = ' '.join(pub.get('keywords', []))
    text = f"{title} {abstract} {citation} {journal} {keywords}".lower()

    tags = set()
    evidence = {}

    def add_tag(tag, reason):
        tags.add(tag)
        if tag not in evidence:
            evidence[tag] = []
        evidence[tag].append(reason)

    # ==========================================
    # 1. METHOD TAGS
    # ==========================================

    # --- EEG ---
    # Look for EEG, ERP, SSVEP, specific ERP waves, oscillations in EEG context
    eeg_patterns = [
        (r'\beeg\b', 'EEG mentioned'),
        (r'electroencephalog\w*', 'electroencephalography'),
        (r'\berps?\b', 'event-related potential(s)'),
        (r'event-related potential|visually evoked potential|evoked potential|\bveps?\b', 'event-related / evoked potential'),
        (r'\bssvep\b', 'SSVEP'),
        (r'steady-state visual\w* evoked', 'SSVEP'),
        (r'\b(n100|n200|p300|p3a|p3b|n400|p600|ern)\b', 'ERP component'),
        (r'visual awareness negativity', 'Visual Awareness Negativity (VAN)'),
        (r'late positivity', 'Late Positivity'),
        (r'error-related negativity', 'ERN'),
        (r'contingent negative variation|\bcnv\b', 'CNV'),
        (r'scalp electrode|64-channel|128-channel|biosemi', 'EEG recording setup'),
        (r'(theta|alpha|beta|gamma)\s+(oscillat\w*|band|power|synchron\w*|phase)', 'neural oscillations/rhythms')
    ]
    for pattern, reason in eeg_patterns:
        if re.search(pattern, text):
            add_tag('EEG', reason)
            break

    # --- fMRI ---
    fmri_patterns = [
        (r'\bfmri\b', 'fMRI mentioned'),
        (r'functional magnetic resonance imaging', 'functional magnetic resonance imaging'),
        (r'\bmri\b', 'MRI mentioned'),
        (r'\bbold\b', 'BOLD response'),
        (r'blood oxygenation level', 'BOLD'),
        (r'fusiform face area|\bffa\b', 'fusiform face area (fMRI)'),
        (r'voxel-based|gray-matter density|voxels?', 'voxel/structural/functional MRI analysis'),
        (r'spinoza centre', 'Spinoza Centre fMRI facility')
    ]
    for pattern, reason in fmri_patterns:
        if re.search(pattern, text):
            add_tag('fMRI', reason)
            break

    # --- MEG ---
    meg_patterns = [
        (r'\bmeg\b', 'MEG mentioned'),
        (r'magnetoencephalog\w*', 'magnetoencephalography'),
        (r'magnetic field\w*', 'magnetic fields (MEG)'),
        (r'axial gradiometer\w*', 'axial gradiometers'),
        (r'neuromagnet\w*', 'neuromagnetism')
    ]
    for pattern, reason in meg_patterns:
        if re.search(pattern, text):
            add_tag('MEG', reason)
            break

    # --- Pupillometry ---
    pupil_patterns = [
        (r'pupil\w*', 'pupil / pupillometry mentioned'),
        (r'pupil-linked', 'pupil-linked arousal'),
        (r'pupil dilation|pupil size|pupil diameter', 'pupillometry'),
        (r'eyelink|eye-tracker|eye tracking', 'eye tracking / pupillometry')
    ]
    for pattern, reason in pupil_patterns:
        if re.search(pattern, text):
            add_tag('Pupillometry', reason)
            break

    # --- Pharmacology ---
    pharm_patterns = [
        (r'pharmacolog\w*', 'pharmacology mentioned'),
        (r'\bgaba\b|gabaa|lorazepam|diazepam', 'GABAergic drug manipulation'),
        (r'ketamine|nmda', 'NMDA / ketamine manipulation'),
        (r'atomoxetine|methylphenidate|catecholamin\w*', 'noradrenergic / dopaminergic manipulation'),
        (r'placebo-controlled|double-blind.*drug', 'pharmacological trial design')
    ]
    for pattern, reason in pharm_patterns:
        if re.search(pattern, text):
            add_tag('Pharmacology', reason)
            break

    # --- Neural Decoding ---
    decoding_patterns = [
        (r'decod\w*', 'decoding mentioned'),
        (r'multivariate pattern|mvpa', 'multivariate pattern analysis (MVPA)'),
        (r'representational similarity analysis|\brsa\b', 'RSA'),
        (r'linear discriminant analysis|\blda\b|support vector machine|\bsvm\b', 'machine learning classifier'),
        (r'adam toolbox|amsterdam decoding', 'ADAM toolbox'),
        (r'pattern classification|neural classifier', 'pattern classification'),
        (r'temporal generalization|generalization across time', 'time-generalized neural decoding'),
        (r'neural represent\w*', 'neural representation tracking')
    ]
    for pattern, reason in decoding_patterns:
        if re.search(pattern, text):
            add_tag('Neural Decoding', reason)
            break

    # ==========================================
    # 2. TOPIC TAGS
    # ==========================================

    # --- Consciousness ---
    conscious_patterns = [
        (r'conscious\w*', 'conscious / consciousness mentioned'),
        (r'unconscious\w*', 'unconscious processing'),
        (r'awareness', 'awareness mentioned'),
        (r'subliminal', 'subliminal priming/presentation'),
        (r'preconscious', 'preconscious processing'),
        (r'masked|masking', 'masking paradigm'),
        (r'phenomen\w*', 'phenomenology'),
        (r'visibility', 'perceptual visibility'),
        (r'access consciousness', 'access consciousness'),
        (r'global workspace|recurrent processing|reentrant', 'theories of consciousness')
    ]
    for pattern, reason in conscious_patterns:
        if re.search(pattern, text):
            add_tag('Consciousness', reason)
            break

    # --- Cognitive Control ---
    control_patterns = [
        (r'cognitive control', 'cognitive control mentioned'),
        (r'inhibitory control|response inhibition|inhibit\w* response', 'inhibitory control'),
        (r'stop-signal|go/no-go|no-go', 'stop-signal / go/no-go task'),
        (r'conflict adaptation|conflict monitoring|response conflict', 'conflict processing'),
        (r'action control|motor control|action selection', 'action selection / control'),
        (r'prefrontal.*control|error monitoring|error detection', 'prefrontal control / error monitoring')
    ]
    for pattern, reason in control_patterns:
        if re.search(pattern, text):
            add_tag('Cognitive Control', reason)
            break

    # --- Decision Making ---
    decision_patterns = [
        (r'decision[- ]making|decision\w*', 'decision making mentioned'),
        (r'drift diffusion|\bddm\b', 'drift diffusion model'),
        (r'evidence accumulation', 'evidence accumulation'),
        (r'criterion|criterion shift', 'decision criterion / shifts'),
        (r'signal detection', 'signal detection theory'),
        (r'perceptual choice\w*|perceptual decision\w*', 'perceptual decisions'),
        (r'response bias|decision bias|perceptual bias|choice bias|criterion bias', 'decision bias')
    ]
    for pattern, reason in decision_patterns:
        if re.search(pattern, text):
            add_tag('Decision Making', reason)
            break

    # --- Perception & Vision ---
    perception_patterns = [
        (r'percept\w*', 'perception mentioned'),
        (r'visual|vision', 'visual processing'),
        (r'illusion\w*', 'visual illusions'),
        (r'bistable|binocular rivalry', 'bistable perception / rivalry'),
        (r'continuous flash suppression|\bcfs\b', 'continuous flash suppression (CFS)'),
        (r'face perception|face processing|fusiform', 'face perception'),
        (r'motion perception|optic flow', 'motion perception'),
        (r'auditory perception|hearing', 'auditory perception')
    ]
    for pattern, reason in perception_patterns:
        if re.search(pattern, text):
            add_tag('Perception & Vision', reason)
            break

    # --- Metacognition & Confidence ---
    meta_patterns = [
        (r'metacognit\w*', 'metacognition mentioned'),
        (r'confidence', 'confidence judgments'),
        (r'subjective rating|perceptual awareness scale|\bpas\b', 'perceptual awareness scale (PAS) / ratings'),
        (r'meta-d\'|type 2', 'metacognitive sensitivity / meta-d\''),
        (r'feeling of knowing|introspect\w*', 'introspective awareness')
    ]
    for pattern, reason in meta_patterns:
        if re.search(pattern, text):
            add_tag('Metacognition & Confidence', reason)
            break

    # --- Hypnosis ---
    hypnosis_patterns = [
        (r'hypno\w*', 'hypnosis / hypnotic mentioned'),
        (r'suggestion\b|post-hypnotic', 'hypnotic suggestion'),
        (r'trance', 'trance state')
    ]
    for pattern, reason in hypnosis_patterns:
        if re.search(pattern, text):
            add_tag('Hypnosis', reason)
            break

    # --- Language & Semantics ---
    lang_patterns = [
        (r'language', 'language mentioned'),
        (r'semantic\w*', 'semantic processing'),
        (r'multiple words|word meaning|lexical', 'words / lexical processing'),
        (r'sentence comprehension|reading', 'sentence reading / comprehension')
    ]
    for pattern, reason in lang_patterns:
        if re.search(pattern, text):
            add_tag('Language & Semantics', reason)
            break

    # --- Disorders of Consciousness ---
    doc_patterns = [
        (r'disorders? of consciousness|\bdoc\b', 'disorders of consciousness'),
        (r'coma\b|vegetative state|unresponsive wakefulness|minimally conscious', 'coma / vegetative / minimally conscious states'),
        (r'severe brain injury', 'severe brain injury')
    ]
    for pattern, reason in doc_patterns:
        if re.search(pattern, text):
            add_tag('Disorders of Consciousness', reason)
            break

    # --- Cognitive Neuroscience ---
    # Foundational CBL tag: applies to cognitive neuroscience studies
    cogneuro_patterns = [
        (r'cognitive neuroscience', 'cognitive neuroscience mentioned'),
        (r'brain|neural|cortical|neurophysiol\w*|electrophysiol\w*', 'neural/brain mechanisms')
    ]
    for pattern, reason in cogneuro_patterns:
        if re.search(pattern, text):
            add_tag('Cognitive Neuroscience', reason)
            break

    # Specific override rules based on known CBL papers
    # 1. pub-78: El Karoui et al. Intracranial study in humans (Auditory novelty) -> Cognitive Neuroscience, EEG (intracranial electrophysiology), Neural Decoding
    # 2. pub-12: Fahrenfort et al. Criterion placement -> Pupillometry, Decision Making, Perception & Vision
    # 3. pub-87: van Loon et al. GABAA agonist -> Pharmacology, Consciousness, EEG, Perception & Vision
    # 4. pub-75: Fahrenfort et al. ADAM toolbox paper -> Neural Decoding, EEG, MEG
    # 5. pub-100: Cohen & van Gaal -> EEG, Cognitive Control, Consciousness

    # Ensure tags are sorted list
    sorted_tags = sorted(list(tags))
    return sorted_tags, evidence

if __name__ == '__main__':
    print("Classifier module loaded successfully.")
