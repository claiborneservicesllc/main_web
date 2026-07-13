#!/usr/bin/env python3
"""
One-time cleanup: remove files accidentally flattened to the repo root
during a zip upload. Every file below is a stray duplicate whose real
copy lives in a subdirectory (blog/, services/, service-area/,
assets/...). Four of them are UTF-16 corrupted and crash the review
automation.

Safety rails:
  - Only touches the explicit list below; never scans or guesses.
  - Only deletes files sitting at the repo ROOT (no path separators).
  - Before deleting each file, verifies a same-named copy exists
    somewhere in a subdirectory; if not, the file is SKIPPED and
    reported instead of deleted.
  - Run with --dry-run (or workflow input) to preview with no changes.
"""
import os, sys

STRAYS = ['banner-excavation-cat305.jpg', 'banner-mulching-cat265-hm316.jpg', 'banner-siteprep-pad.jpg', 'best-time-of-year-for-tree-removal.html', 'brentwood-tn.html', 'columbia-tn.html', 'driveway-grading.html', 'emergency-tree-service.html', 'equip-haulotte-55xa-boomlift.jpg', 'equip-miniskid-kubota-grapple.jpg', 'equip-mulcher-cat265-hm316.jpg', 'equip-skidsteer-cat265-grapple.jpg', 'equip-stumpgrinder-cat265-fae.jpg', 'excav-driveway-cut.jpg', 'excav-stone-trench-bobcat.jpg', 'excav-trench-horse-fence.jpg', 'excav-utility-trench-tree.jpg', 'excavation.html', 'favicon-192.png', 'favicon-512.png', 'forest-hills-tn.html', 'forestry-mulching.html', 'franklin-tn.html', 'how-to-choose-a-tree-service-company.html', 'land-cat265-grapple-burn.jpg', 'land-cat265-rake-rootball.jpg', 'land-clearing-vs-forestry-mulching.html', 'land-clearing.html', 'leipers-fork-tn.html', 'logo.png', 'mt-pleasant-tn.html', 'mulch-trail-cat265-pov.jpg', 'nashville-tn.html', 'nolensville-tn.html', 'oak-hill-tn.html', 'og-default.jpg', 'prepare-property-for-storm-season.html', 'signs-you-need-emergency-tree-service.html', 'site-prep-checklist-for-new-construction.html', 'site-preparation.html', 'spring-hill-tn.html', 'stump-grinding-vs-stump-removal.html', 'stump-grinding.html', 'styles.css', 'thompsons-station-tn.html', 'tree-bucket-storm-franklin.jpg', 'tree-haulotte-drone-backyard.jpg', 'tree-removal-cost-middle-tennessee.html', 'tree-removal-permit-franklin-tn.html', 'tree-removal-vs-tree-trimming.html', 'tree-removal.html', 'tree-services.html', 'tree-trimming.html', 'what-to-expect-driveway-grading-project.html']

def find_twin(name):
    for dirpath, dirnames, filenames in os.walk("."):
        dirnames[:] = [d for d in dirnames if d not in (".git",)]
        if dirpath == ".":
            continue
        if name in filenames:
            return os.path.join(dirpath, name)
    return None

def main():
    dry = "--dry-run" in sys.argv
    deleted, skipped, absent = [], [], []
    for name in STRAYS:
        if "/" in name or "\\" in name:
            skipped.append((name, "not a root-level path"))
            continue
        if not os.path.isfile(name):
            absent.append(name)
            continue
        twin = find_twin(name)
        if twin is None:
            skipped.append((name, "no subdirectory copy found"))
            continue
        if dry:
            print("[dry-run] would delete ./%s  (real copy: %s)" % (name, twin))
        else:
            os.remove(name)
            print("deleted ./%s  (real copy: %s)" % (name, twin))
        deleted.append(name)
    print()
    print("Summary: %d %s, %d already absent, %d skipped"
          % (len(deleted), "would be deleted" if dry else "deleted", len(absent), len(skipped)))
    for name, why in skipped:
        print("  SKIPPED %s -- %s" % (name, why))
    if skipped:
        sys.exit(2)

if __name__ == "__main__":
    main()
