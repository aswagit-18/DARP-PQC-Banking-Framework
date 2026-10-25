# Final PQC Banking Risk Framework Architecture

```mermaid
flowchart TD
    A[Digital Banking Ecosystem]
    B[Cryptographic Asset Inventory]
    C[Multi-Tier Dependency Graph\nService -> Internal -> Third-Party -> Sub-Tier]
    D[Direct Contextual Quantum-Risk Score]
    E[Strongest Dependency Path Extraction]
    F[Path-Aware Quantum Risk Propagation\nPR = DR x Product of dependency strengths]
    G[Inherited Service Risk]
    H[Total Service Risk]
    I[Ecosystem Risk ER\nCriticality-weighted service risk]
    J[Counterfactual PQC Remediation Simulation]
    K[Marginal Ecosystem Risk Reduction\nDelta ER = ER_before - ER_after]
    L[Cost-Aware Priority\nDelta ER / Migration Cost]
    M[Dynamic Recalculation After Each Migration]
    N[Explainable PQC Migration Roadmap]

    A --> B --> C --> D --> E --> F --> G --> H --> I --> J --> K --> L --> M --> N
    M --> J
```

The feedback loop from dynamic recalculation to remediation simulation is central: after each selected action, all remaining candidates are re-evaluated against the updated ecosystem state.
