---
title: "google /      langextract"
url: "https://github.com/google/langextract"
source: "NewsNow 中文热点"
date: 2026-02-11
score: 100.0
---

# google /      langextract

**来源**: [NewsNow 中文热点](https://github.com/google/langextract) | **热度**: 100.0

## 原文内容

Title: GitHub - google/langextract: A Python library for extracting structured information from unstructured text using LLMs with precise source grounding and interactive visualization.

URL Source: http://github.com/google/langextract

Markdown Content:
[![Image 1: LangExtract Logo](https://raw.githubusercontent.com/google/langextract/main/docs/_static/logo.svg)](https://github.com/google/langextract)

LangExtract
-----------

[](http://github.com/google/langextract#langextract)
[![Image 2: PyPI version](https://camo.githubusercontent.com/ec4faf4cff274784c4a1d3fdef978a21a911abb7bbe06e64c5283a0ad9a8afd8/68747470733a2f2f696d672e736869656c64732e696f2f707970692f762f6c616e67657874726163742e737667)](https://pypi.org/project/langextract/)[![Image 3: GitHub stars](https://camo.githubusercontent.com/c47bd46dd8c1e8c5ebde9fa9b19ca9444f2536a66ac86f87c7a735039bc57750/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f73746172732f676f6f676c652f6c616e67657874726163742e7376673f7374796c653d736f6369616c266c6162656c3d53746172)](https://github.com/google/langextract)[![Image 4: Tests](https://github.com/google/langextract/actions/workflows/ci.yaml/badge.svg)](https://github.com/google/langextract/actions/workflows/ci.yaml/badge.svg)[![Image 5: DOI](https://camo.githubusercontent.com/3fe6bcea397afebfaad025f92a98f82cf4d84b5ef8a792faf660580d60b26082/68747470733a2f2f7a656e6f646f2e6f72672f62616467652f444f492f31302e353238312f7a656e6f646f2e31373031353038392e737667)](https://doi.org/10.5281/zenodo.17015089)

Table of Contents
-----------------

[](http://github.com/google/langextract#table-of-contents)
*   [Introduction](http://github.com/google/langextract#introduction)
*   [Why LangExtract?](http://github.com/google/langextract#why-langextract)
*   [Quick Start](http://github.com/google/langextract#quick-start)
*   [Installation](http://github.com/google/langextract#installation)
*   [API Key Setup for Cloud Models](http://github.com/google/langextract#api-key-setup-for-cloud-models)
*   [Adding Custom Model Providers](http://github.com/google/langextract#adding-custom-model-providers)
*   [Using OpenAI Models](http://github.com/google/langextract#using-openai-models)
*   [Using Local LLMs with Ollama](http://github.com/google/langextract#using-local-llms-with-ollama)
*   [More Examples](http://github.com/google/langextract#more-examples)
    *   [_Romeo and Juliet_ Full Text Extraction](http://github.com/google/langextract#romeo-and-juliet-full-text-extraction)
    *   [Medication Extraction](http://github.com/google/langextract#medication-extraction)
    *   [Radiology Report Structuring: RadExtract](http://github.com/google/langextract#radiology-report-structuring-radextract)

*   [Community Providers](http://github.com/google/langextract#community-providers)
*   [Contributing](http://github.com/google/langextract#contributing)
*   [Testing](http://github.com/google/langextract#testing)
*   [Disclaimer](http://github.com/google/langextract#disclaimer)

Introduction
------------

[](http://github.com/google/langextract#introduction)
LangExtract is a Python library that uses LLMs to extract structured information from unstructured text documents based on user-defined instructions. It processes materials such as clinical notes or reports, identifying and organizing key details while ensuring the extracted data corresponds to the source text.

Why LangExtract?
----------------

[](http://github.com/google/langextract#why-langextract)
1.   **Precise Source Grounding:** Maps every extraction to its exact location in the source text, enabling visual highlighting for easy traceability and verification.
2.   **Reliable Structured Outputs:** Enforces a consistent output schema based on your few-shot examples, leveraging controlled generation in supported models like Gemini to guarantee robust, structured results.
3.   **Optimized for Long Documents:** Overcomes the "needle-in-a-haystack" challenge of large document extraction by using an optimized strategy of text chunking, parallel processing, and multiple passes for higher recall.
4.   **Interactive Visualization:** Instantly generates a self-contained, interactive HTML file to visualize and review thousands of extracted entities in their original context.
5.   **Flexible LLM Support:** Supports your preferred models, from cloud-based LLMs like the Google Gemini family to local open-source models via the built-in Ollama interface.
6.   **Adaptable to Any Domain:** Define extraction tasks for any domain using just a few examples. LangExtract adapts to your needs without requiring any model fine-tuning.
7.   **Leverages LLM World Knowledge:** Utilize precise prompt wording and few-shot examples to influence how the extraction task may utilize LLM knowledge. The accuracy of any inferred information and its adherence to the task specification are contingent upon the selected LLM, the complexity of the task, the clarity of the prompt instructions, and the nature of the prompt exampl

---
*自动采集于 2026-02-11 23:00:50 (北京时间)*
