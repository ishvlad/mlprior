import math


############################################
# Mapping from 'color_name' to 'RGB color' #
############################################

class _color:
    def __init__(self, colors):
        for k, v in colors.items():
            setattr(self, k, v)

    def get_colors_code(self, num=-1):
        all_colors = list(set(self.__dict__.values()))

        if num == -1:
            return all_colors
        elif num <= len(all_colors):
            return all_colors[:num]
        else:
            return (all_colors * math.ceil(num/len(all_colors)))[:num]

GLOBAL__CATEGORIES = {
    "cs.AI": "Artificial Intelligence",
    "cs.AR": "Hardware Architecture",
    "cs.CC": "Computational Complexity",
    "cs.CG": "Computational Geometry",
    "cs.CE": "Computational Engineering, Finance, and Science",
    "cs.CL": "Computation and Language",
    "cs.CV": "Computer Vision and Pattern Recognition",
    "cs.CY": "Computers and Society",
    "cs.CR": "Cryptography and Security",
    "cs.DB": "Databases",
    "cs.DS": "Data Structures and Algorithms",
    "cs.DL": "Digital Libraries",
    "cs.DM": "Discrete Mathematics",
    "cs.DC": "Distributed, Parallel, and Cluster Computing",
    "cs.ET": "Emerging Technologies",
    "cs.FL": "Formal Languages and Automata Theory",
    "cs.GT": "Computer Science and Game Theory",
    "cs.GL": "General Literature",
    "cs.GR": "Graphics",
    "cs.HC": "Human-Computer Interaction",
    "cs.IR": "Information Retrieval",
    "cs.IT": "Information Theory",
    "cs.LG": "Machine Learning",
    "cs.LO": "Logic in Computer Science",
    "cs.MS": "Mathematical Software",
    "cs.MA": "Multiagent Systems",
    "cs.MM": "Multimedia",
    "cs.NI": "Networking and Internet Architecture",
    "cs.NE": "Neural and Evolutionary Computation",
    "cs.NA": "Numerical Analysis",
    "cs.OS": "Operating Systems",
    "cs.OH": "Other",
    "cs.PF": "Performance",
    "cs.PL": "Programming Languages",
    "cs.RO": "Robotics",
    "cs.SI": "Social and Information Networks",
    "cs.SE": "Software Engineering",
    "cs.SD": "Sound",
    "cs.SC": "Symbolic Computation",
    "cs.SY": "Systems and Control",

    'eess.AS': "Audio and Speech Processing",
    'eess.IV': "Image and Video Processing",
    'eess.SP': "Signal Processing",

    'gr-qc': "General Relativity and Quantum Cosmology",

    'math.AG': "Algebraic Geometry",
    'math.AT': "Algebraic Topology",
    'math.AP': "Analysis of PDEs",
    'math.CT': "Category Theory",
    'math.CA': "Classical Analysis and ODEs",
    'math.CO': "Combinatorics",
    'math.AC': "Commutative Algebra",
    'math.CV': "Complex Variables",
    'math.DG': "Differential Geometry",
    'math.DS': "Dynamical Systems",
    'math.FA': "Functional Analysis",
    'math.GM': "General Mathematics",
    'math.GN': "General Topology",
    'math.GT': "Geometric Topology",
    'math.GR': "Group Theory",
    'math.HO': "History and Overview",
    'math.IT': "Information Theory",
    'math.KT': "K-Theory and Homology",
    'math.LO': "Logic",
    'math.MP': "Mathematical Physics",
    'math.MG': "Metric Geometry",
    'math.NT': "Number Theory",
    'math.NA': "Numerical Analysis",
    'math.OA': "Operator Algebras",
    'math.OC': "Optimization and Control",
    'math.PR': "Probability",
    'math.QA': "Quantum Algebra",
    'math.RT': "Representation Theory",
    'math.RA': "Rings and Algebras",
    'math.SP': "Spectral Theory",
    'math.ST': "Statistics Theory",
    'math.SG': "Symplectic Geometry",

    'math-ph': "Mathematical Physics",

    'physics.acc-ph': "Accelerator Physics",
    'physics.app-ph': "Applied Physics",
    'physics.ao-ph': "Atmospheric and Oceanic Physics",
    'physics.atom-ph': "Atomic Physics",
    'physics.atm-clus': "Atomic and Molecular Clusters",
    'physics.bio-ph': "Biological Physics",
    'physics.chem-ph': "Chemical Physics",
    'physics.class-ph': "Classical Physics",
    'physics.comp-ph': "Computational Physics",
    'physics.data-an': "Data Analysis, Statistics and Probability",
    'physics.flu-dyn': "Fluid Dynamics",
    'physics.gen-ph': "General Physics",
    'physics.geo-ph': "Geophysics",
    'physics.hist-ph': "History and Philosophy of Physics",
    'physics.ins-det': "Instrumentation and Detectors",
    'physics.med-ph': "Medical Physics",
    'physics.optics': "Optics",
    'physics.ed-ph': "Physics Education",
    'physics.soc-ph': "Physics and Society",
    'physics.plasm-ph': "Plasma Physics",
    'physics.pop-ph': "Popular Physics",
    'physics.space-ph': "Space Physics",

    'stat.AP': "Applications",
    'stat.CO': "Computation",
    'stat.ML': "Machine Learning",
    'stat.ME': "Methodology",
    'stat.OT': "Other Statistics",
    'stat.TH': "Statistics Theory",

    'q-bio.BM': "Biomolecules",
    'q-bio.CB': "Cell Behavior",
    'q-bio.GN': "Genomics",
    'q-bio.MN': "Molecular Networks",
    'q-bio.NC': "Neurons and Cognition",
    'q-bio.OT': "Other Quantitative Biology",
    'q-bio.PE': "Populations and Evolution",
    'q-bio.QM': "Quantitative Methods",
    'q-bio.SC': "Subcellular Processes",
    'q-bio.TO': "Tissues and Organs",

    'q-fin.CP': "Computational Finance",
    'q-fin.EC': "Economics",
    'q-fin.GN': "General Finance",
    'q-fin.MF': "Mathematical Finance",
    'q-fin.PM': "Portfolio Management",
    'q-fin.PR': "Pricing of Securities",
    'q-fin.RM': "Risk Management",
    'q-fin.ST': "Statistical Finance",
    'q-fin.TR': "Trading and Market Microstructure"
}
GLOBAL__COLORS = _color({
    'sb_blue':      '#4e73df',
    'sb_cyan':      '#36b9cc',
    'sb_gray':      '#858796',
    'sb_green':     '#1cc88a',
    'sb_indigo':    '#6610f2',
    'sb_orange':    '#fd7e14',
    'sb_pink':      '#e83e8c',
    'sb_purple':    '#6f42c1',
    'sb_red':       '#e74a3b',
    'sb_teal':      '#20c9a6',
    'sb_yellow':    '#f6c23e',
})

VISUALIZATION__INITIAL_NUM_BARS = 12
