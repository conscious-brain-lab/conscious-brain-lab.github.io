#!/usr/bin/env python3
"""
Publication Tag Enrichment & Synchronization Script
Audits and updates all publications in content/publications/*.json and data/publications.json
with accurate methods and research topic tags.
"""

import json
import glob
import re
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from local_cms_server import sync_collections_to_data
from audit.classify_publications import analyze_paper, VALID_TOPICS

# Specific manual overrides for seminal CBL papers where methodology or nuances
# are verified through known CBL publications
EXPERT_OVERRIDES = {
    # pub-75: Fahrenfort et al. (2018) ADAM: Amsterdam Decoding and Modeling toolbox
    "pub-75": ["Neural Decoding", "EEG", "MEG", "Cognitive Neuroscience"],
    # pub-78: El Karoui et al. (2015) Auditory novelty intracranial study
    "pub-78": ["Neural Decoding", "EEG", "Cognitive Neuroscience", "Perception & Vision"],
    # pub-87: van Loon et al. (2012) GABAA Agonist Reduces Visual Awareness: A Masking-EEG Experiment
    "pub-87": ["Pharmacology", "EEG", "Consciousness", "Perception & Vision", "Cognitive Neuroscience"],
    # pub-10: Adaptive arousal regulation: Pharmacologically shifting the peak...
    "pub-10": ["Pharmacology", "Pupillometry", "Decision Making", "Cognitive Neuroscience"],
    # pub-12: Fahrenfort et al. Criterion placement...
    "pub-12": ["Pupillometry", "Decision Making", "Perception & Vision", "Consciousness", "Cognitive Neuroscience"],
    # pub-21: Nuiten et al. (2023) Catecholaminergic neuromodulation and selective attention
    "pub-21": ["Pharmacology", "Pupillometry", "Decision Making", "Perception & Vision", "Cognitive Neuroscience"],
    # pub-34: Seijdel et al. (2021) On the necessity of recurrent processing during object recognition
    "pub-34": ["Neural Decoding", "EEG", "Perception & Vision", "Cognitive Neuroscience"],
    # pub-35: de Gee et al. (2021) Pupil dilation and the slow wave ERP reflect surprise about choices and outcomes
    "pub-35": ["Pupillometry", "EEG", "Decision Making", "Cognitive Neuroscience"],
    # pub-36: Alilović et al. (2021) Representational dynamics preceding conscious visual perception
    "pub-36": ["Neural Decoding", "EEG", "Consciousness", "Perception & Vision", "Cognitive Neuroscience"],
    # pub-37: Alilović et al. (2021) Subjective visibility report is facilitated by conscious prediction
    "pub-37": ["Consciousness", "Metacognition & Confidence", "Perception & Vision", "Cognitive Neuroscience"],
    # pub-38: van Driel, Olivers & Fahrenfort (2021) High-pass filtering artifacts in multivariate classification
    "pub-38": ["Neural Decoding", "EEG", "MEG", "Cognitive Neuroscience"],
    # pub-42: Canales-Johnson et al. (2020) Subcortical and cortico-cortical connectivity during hypnosis
    "pub-42": ["Hypnosis", "EEG", "Consciousness", "Cognitive Neuroscience"],
    # pub-46: Baas et al. (2020) Methylphenidate does not affect convergent and divergent thinking
    "pub-46": ["Pharmacology", "Cognitive Control", "Cognitive Neuroscience"],
    # pub-73: Jiang et al. (2015) EEG neural oscillatory dynamics reveal semantic and response conflict
    "pub-73": ["Language & Semantics", "Cognitive Control", "EEG", "Cognitive Neuroscience"],
    # pub-74: Jiang et al. (2015) Conflict awareness dissociates theta-band neural dynamics
    "pub-74": ["Consciousness", "Cognitive Control", "EEG", "Cognitive Neuroscience"],
    # pub-79: van Gaal et al. (2014) Can the meaning of multiple words be integrated unconsciously?
    "pub-79": ["Language & Semantics", "Consciousness", "EEG", "Cognitive Neuroscience"],
    # pub-80: Cohen & van Gaal (2014) Subthreshold muscle twitches dissociate oscillatory neural signatures
    "pub-80": ["EEG", "Cognitive Control", "Cognitive Neuroscience"],
    # pub-84: Fahrenfort et al. (2013) Neuronal integration in visual cortex elevates face category tuning
    "pub-84": ["EEG", "Consciousness", "Perception & Vision", "Cognitive Neuroscience"],
    # pub-86: Fahrenfort & van Gaal (2012) Fusiform face area comment
    "pub-86": ["Consciousness", "fMRI", "Perception & Vision", "Cognitive Neuroscience"],
    # pub-90: de Lange et al. (2011) How Awareness Changes the Relative Weights of Evidence During Human Decision-Making (MEG)
    "pub-90": ["MEG", "Consciousness", "Decision Making", "Cognitive Neuroscience"],
    # pub-94: Weeda et al. (2010) Functional connectivity analysis of fMRI data
    "pub-94": ["fMRI", "Cognitive Neuroscience"],
    # pub-96: van Gaal et al. (2010) Pre-SMA Gray-matter Density Predicts Individual Differences...
    "pub-96": ["fMRI", "Cognitive Control", "Consciousness", "Cognitive Neuroscience"],
    # pub-98: van Gaal et al. (2010) Unconscious Activation of the Prefrontal No-Go Network (fMRI)
    "pub-98": ["fMRI", "Cognitive Control", "Consciousness", "Cognitive Neuroscience"],
    # pub-100: Cohen, van Gaal et al. (2009) Unconscious errors enhance prefrontal-occipital theta phase synchronization (EEG)
    "pub-100": ["EEG", "Consciousness", "Cognitive Control", "Cognitive Neuroscience"],
    # pub-102: van Gaal et al. (2008) Frontal Cortex Mediates Unconsciously Triggered Inhibitory Control (fMRI/EEG)
    "pub-102": ["fMRI", "Cognitive Control", "Consciousness", "Cognitive Neuroscience"],
    # pub-104: Fahrenfort et al. (2007) Masking Disrupts Reentrant Processing in Human Visual Cortex (EEG)
    "pub-104": ["EEG", "Consciousness", "Perception & Vision", "Cognitive Neuroscience"],
    # pub-69: van Loon et al. (2016) NMDA Receptor Antagonist Ketamine Impairs Recurrent Processing and Conscious Perception
    "pub-69": ["Pharmacology", "EEG", "Consciousness", "Perception & Vision", "Cognitive Neuroscience"],
    # pub-68: Boot et al. (2017) Creative cognition and dopaminergic modulation
    "pub-68": ["Pharmacology", "Cognitive Control", "Cognitive Neuroscience"],
    # pub-67: Boot et al. (2017) Widespread neural oscillations in the delta, theta, alpha, and beta bands
    "pub-67": ["EEG", "Cognitive Neuroscience"],
    # pub-70: Vandenbroucke et al. (2014) Prior knowledge impacts earliest stages of visual processing (EEG)
    "pub-70": ["EEG", "Perception & Vision", "Cognitive Neuroscience"],
    # pub-82: Jiang et al. (2013) Electrophysiological correlates of block-wise strategic adaptations (EEG)
    "pub-82": ["EEG", "Consciousness", "Cognitive Control", "Cognitive Neuroscience"],
    # pub-28: Overbeek et al. (2022) Prognosis and recovery in disorders of consciousness
    "pub-28": ["Disorders of Consciousness", "Consciousness", "Cognitive Neuroscience"],
    # pub-31: Dijkstra et al. (2021) Overlap in externally and internally generated visual representations
    "pub-31": ["Neural Decoding", "Perception & Vision", "Cognitive Neuroscience"],
    # pub-99: van Gaal et al. (2009) Dissociating consciousness from inhibitory control: stop-signal task
    "pub-99": ["Cognitive Control", "Consciousness", "Cognitive Neuroscience"],
    # pub-30: Nuiten et al. (2021) Preserved sensory processing but hampered conflict detection (EEG)
    "pub-30": ["Cognitive Control", "Consciousness", "EEG", "Neural Decoding", "Perception & Vision", "Cognitive Neuroscience"],
    # pub-43: Kloosterman et al. (2020) Boosts in brain signal variability track liberal shifts in decision bias (EEG)
    "pub-43": ["EEG", "Decision Making", "Perception & Vision", "Cognitive Neuroscience"],
    # pub-47: Kloosterman et al. (2019) Humans strategically shift decision bias (Pupillometry/EEG)
    "pub-47": ["Pupillometry", "EEG", "Decision Making", "Perception & Vision", "Cognitive Neuroscience"],
    # pub-62: Meijs et al. (2018) Dynamic Interactions between Top-Down Expectations and Conscious Awareness (EEG)
    "pub-62": ["EEG", "Consciousness", "Perception & Vision", "Cognitive Neuroscience"]
}

def audit_and_apply(dry_run=True):
    abstracts_file = 'scripts/audit/publications_with_abstracts.json'
    if not os.path.exists(abstracts_file):
        print(f"Error: {abstracts_file} does not exist.")
        return

    with open(abstracts_file) as f:
        publications = json.load(f)

    print(f"Loaded {len(publications)} publications from {abstracts_file}.")
    
    updated_records = []
    stats = {t: 0 for t in VALID_TOPICS}
    changes_count = 0

    for pub in publications:
        pub_id = pub['id']
        old_topics = sorted(pub.get('existing_topics', []))

        # Check expert overrides first
        if pub_id in EXPERT_OVERRIDES:
            new_topics = sorted(EXPERT_OVERRIDES[pub_id])
            reasons = ["Expert curation from paper methodology"]
        else:
            classified_topics, evidence = analyze_paper(pub)
            # Ensure at least Cognitive Neuroscience if general CBL paper
            if not classified_topics:
                classified_topics = ["Cognitive Neuroscience"]
            
            # Merge with existing topics to not drop valid human-curated tags unless contradictory
            merged = set(classified_topics)
            for ot in old_topics:
                if ot in VALID_TOPICS:
                    merged.add(ot)
            new_topics = sorted(list(merged))
            reasons = [f"{k}: {', '.join(v)}" for k, v in evidence.items()]

        for t in new_topics:
            stats[t] += 1

        is_different = old_topics != new_topics
        if is_different:
            changes_count += 1

        updated_records.append({
            'id': pub_id,
            'title': pub.get('title'),
            'old_topics': old_topics,
            'new_topics': new_topics,
            'reasons': reasons,
            'is_different': is_different
        })

    print(f"\n--- AUDIT SUMMARY ---")
    print(f"Total publications audited: {len(publications)}")
    print(f"Publications with tag updates: {changes_count}")
    print(f"\nNew Topic / Method Distribution:")
    for t in sorted(stats.keys(), key=lambda x: -stats[x]):
        print(f"  {t:26s}: {stats[t]}")

    if dry_run:
        print("\nDRY RUN: No files modified.")
        return updated_records

    # Apply changes to content/publications/*.json
    print("\nApplying changes to content/publications/*.json...")
    for rec in updated_records:
        pub_file = f"content/publications/{rec['id']}.json"
        if not os.path.exists(pub_file):
            print(f"Warning: {pub_file} not found, skipping.")
            continue
        with open(pub_file, 'r') as fp:
            data = json.load(fp)
        data['topics'] = rec['new_topics']
        with open(pub_file, 'w') as fp:
            json.dump(data, fp, indent=2)

    # Sync to data/publications.json
    print("\nSynchronizing collections to data/publications.json...")
    sync_collections_to_data()
    print("Synchronization complete!")

    # Write audit report markdown
    report_file = 'scripts/audit/audit_report.md'
    with open(report_file, 'w') as out:
        out.write("# CBL Publications Tag Audit Report\n\n")
        out.write(f"- Total Publications: {len(publications)}\n")
        out.write(f"- Publications Updated: {changes_count}\n\n")
        out.write("## Topic & Method Distribution\n\n")
        out.write("| Topic / Method | Count |\n| --- | ---: |\n")
        for t in sorted(stats.keys(), key=lambda x: -stats[x]):
            out.write(f"| {t} | {stats[t]} |\n")
        out.write("\n## Publication Changes\n\n")
        for rec in updated_records:
            if rec['is_different']:
                out.write(f"### `{rec['id']}`: {rec['title']}\n")
                out.write(f"- **Old**: {', '.join(rec['old_topics']) if rec['old_topics'] else '*(none)*'}\n")
                out.write(f"- **New**: {', '.join(rec['new_topics'])}\n")
                if rec['reasons']:
                    out.write(f"- **Evidence**: {'; '.join(rec['reasons'])}\n")
                out.write("\n")
    print(f"Audit report written to {report_file}")
    return updated_records

if __name__ == '__main__':
    dry = '--apply' not in sys.argv
    audit_and_apply(dry_run=dry)
