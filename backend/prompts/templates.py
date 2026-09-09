QUERY_UNDERSTANDING_PROMPT = """You are an expert academic research assistant.

Analyze the following natural language research query and extract structured information.

Query: {query}

Respond ONLY with valid JSON matching this exact schema:
{{
  "research_topic": "main research topic",
  "subtopics": ["subtopic1", "subtopic2"],
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "publication_year_range": {{"from": 2020, "to": 2025}},
  "conferences": ["conference1", "conference2"],
  "paper_type": "survey|empirical|theoretical|benchmark|review",
  "search_intent": "find latest|compare approaches|understand concepts|find datasets",
  "domain": "computer science|biology|medicine|physics|mathematics|other"
}}
"""

QUERY_EXPANSION_PROMPT = """You are an expert research librarian specializing in academic search.

Given the following research topic and keywords, generate expanded search queries.

Research Topic: {research_topic}
Keywords: {keywords}
Subtopics: {subtopics}

Respond ONLY with valid JSON matching this exact schema:
{{
  "synonyms": ["synonym1", "synonym2"],
  "alternative_keywords": ["alt1", "alt2", "alt3"],
  "boolean_queries": [
    "(keyword1 AND keyword2) OR keyword3",
    "keyword1 AND (synonym1 OR synonym2)"
  ],
  "academic_queries": [
    "arxiv: keyword1 keyword2",
    "semantic scholar: topic subtopic"
  ],
  "expanded_topics": ["expanded topic 1", "expanded topic 2"]
}}
"""

SUMMARIZATION_PROMPT = """You are an expert academic paper analyst.

Using the retrieved text chunks from the paper, generate a comprehensive, highly structured summary and abstract.
IMPORTANT: You MUST populate ALL fields in the JSON. If a section is not explicitly labeled with headers in the text, you MUST infer it or provide a best educated guess based on the abstract, introduction, and contents of the paper. Under NO circumstances should any field be null, empty, or contain "Not specified", "N/A", or similar placeholder text. Every single field MUST contain a meaningful, detailed summary or list of points inferred from the paper.

Paper Title: {title}
Authors: {authors}

Retrieved Chunks:
{chunks}

Respond ONLY with valid JSON matching this exact schema:
{{
  "abstract": "A clear, comprehensive, and well-structured academic abstract detailing the problem statement, background, core approach, methodology, key findings, and contributions.",
  "summary_100_words": "A concise, high-impact 100-word executive summary of the paper.",
  "detailed_summary": "An in-depth multi-paragraph structured summary of the entire paper covering research background, key innovation, system architecture, methodology, experimental results, and practical impact.",
  "methodology": "Detailed explanation of the methodology, techniques, algorithms, mathematical formulation, or framework proposed in the paper.",
  "architecture": "Description of the model, framework, system pipeline, or conceptual architecture setup.",
  "dataset": "Datasets, benchmarks, corpora, or experimental data sources utilized for evaluation.",
  "experiments": "Details of the experimental setup, baseline comparisons, evaluation metrics, and implementation details.",
  "results": "Core quantitative and qualitative results, metrics achieved, state-of-the-art comparisons, and empirical findings.",
  "strengths": ["Key technical strength 1", "Key technical strength 2"],
  "weaknesses": ["Potential weakness or trade-off 1", "Potential weakness or trade-off 2"],
  "limitations": ["Limitation or scope boundary 1", "Limitation or scope boundary 2"],
  "future_work": ["Promising future research direction 1", "Promising future research direction 2"],
  "applications": ["Real-world application 1", "Real-world application 2"],
  "key_contributions": ["Major contribution 1", "Major contribution 2"]
}}
"""

RESEARCH_GAP_PROMPT = """You are an expert academic researcher analyzing multiple research papers.

Based on the following paper summaries and abstracts, generate a comprehensive research gap analysis.

Papers:
{papers}

Respond ONLY with valid JSON matching this exact schema:
{{
  "current_trends": ["trend1", "trend2", "trend3"],
  "open_challenges": ["challenge1", "challenge2"],
  "research_gaps": ["gap1", "gap2", "gap3"],
  "future_directions": ["direction1", "direction2"],
  "potential_thesis_ideas": ["idea1", "idea2"],
  "novel_ideas": ["novel idea1", "novel idea2"],
  "consensus_findings": ["finding1", "finding2"],
  "conflicting_results": ["conflict1", "conflict2"]
}}
"""

RECOMMENDATION_PROMPT = """You are an expert academic research advisor.

Based on the following research papers and their metadata, generate comprehensive recommendations.

Papers:
{papers}

Research Topic: {research_topic}

Respond ONLY with valid JSON matching this exact schema:
{{
  "related_papers": [
    {{"title": "paper title", "reason": "why it's related"}}
  ],
  "survey_papers": ["survey paper suggestion 1", "survey paper suggestion 2"],
  "code_repositories": ["repo1", "repo2"],
  "recommended_datasets": ["dataset1", "dataset2"],
  "key_authors": ["author1", "author2"],
  "recommended_conferences": ["conference1", "conference2"],
  "learning_path": ["step1", "step2", "step3"]
}}
"""

METADATA_EXTRACTION_PROMPT = """You are an academic metadata extractor.

Given the following web page snippet/content about a research paper, extract structured metadata.
If a field is not found, use null.

Content:
{content}

URL: {url}

Respond ONLY with valid JSON:
{{
  "title": "paper title",
  "authors": ["Author One", "Author Two"],
  "year": 2024,
  "publisher": "publisher name",
  "conference": "conference/journal name",
  "doi": "doi string or null",
  "abstract": "abstract text",
  "keywords": ["keyword1", "keyword2"],
  "citation_count": null,
  "license": "license or null",
  "github_url": "url or null",
  "dataset": "dataset name or null",
  "pdf_url": "direct pdf url or null",
  "thumbnail": "image url or null"
}}
"""

RAG_CHAT_PROMPT = """You are a research paper expert assistant.

Answer the user's question using ONLY the following retrieved chunks from the paper.
Do NOT hallucinate or add information not present in the chunks.
If the answer is not found in the chunks, say "I couldn't find this information in the paper."

Paper Title: {title}

Retrieved Chunks:
{chunks}

User Question: {question}

Provide a clear, concise, and accurate answer based solely on the retrieved content.
"""
