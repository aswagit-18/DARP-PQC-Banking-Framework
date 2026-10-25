DEPENDENCY AWARE PQC MIGRATION FRAMEWORK FOR DIGITAL BANKING
Full system architecture figure — IEEE-style manuscript asset

FILES
- DARP_PQC_Full_System_Architecture.png : publication-ready raster image (320 dpi)
- DARP_PQC_Full_System_Architecture.svg : editable vector figure
- DARP_PQC_Full_System_Architecture.pdf : vector PDF proof
- IEEE_PQC_Architecture_Figure.py : full source code (run in VS Code)

CREATE OR EDIT IN VS CODE (Mac)
1. Copy IEEE_PQC_Architecture_Figure.py to the top level of
   ~/Downloads/PQC_Banking_Risk_Framework_COMPLETE/
2. Open that project folder in VS Code.
3. In the VS Code Terminal:
   source .venv/bin/activate
   python -m pip install matplotlib
   python IEEE_PQC_Architecture_Figure.py
4. Open:
   open PQC_Architecture_Figure/DARP_PQC_Full_System_Architecture.png

TO INSERT IN YOUR IEEE ACCESS WORD PAPER
- Place the figure in the 'System Architecture' or 'Proposed Framework' section.
- For full-width (two-column-spanning) figures, use an appropriately configured
  full-width section of the document, then return to two columns afterward.
- Insert PNG from Word > Insert > Pictures, or SVG if Word SVG support is available.
- Preserve aspect ratio; do not stretch or crop labels.
- Suggested caption:
  'Overall architecture of the dependency-aware post-quantum migration
   framework. A banking asset inventory is validated and modeled as a
   multi-tier directed dependency graph. Service-weighted risk supports
   budgeted dynamic remediation planning and risk-bound cryptographic
   policy selection. The transaction gateway combines ML-KEM, ML-DSA,
   HKDF, AES-256-GCM, role-based access control, policy-epoch binding,
   and simulated signed third-party and sub-tier acknowledgements.
   Planning and transaction evaluation outputs are recorded separately.'

NOTES
- This is a software-architecture diagram, not a measured performance chart.
- The 2,100 assets, 60 services and 2,862 dependency rows are synthetic.
- Supplier acknowledgements in this research prototype are simulated and do
  not certify actual external bank/vendor deployments.
