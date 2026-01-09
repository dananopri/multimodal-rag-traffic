# multimodal-rag-traffic
A multimodal RAG assistant that using text and images teaches traffic rules and signs. 

### Problem & Users
The goal of this project is to build a multimodal retrieval-based system that helps users understand traffic signs by combining textual explanations with visual examples.
Target users are anyone who wants to learn traffic rules and signs. 

### MVP Scope
The system will accept quaries about traffic rules, retrieve relevant textual explanations, retrieve and display corresponding images of traffic signs, present text and images together in a single response.

The system **will not** do any traffic sign detection or real-time video processing. The system focuses only on retrieval and explanation.
### Content & Data
The system uses Ukrainian Traffic signs, scraped from the following website: \
`https://www.rhinocarhire.com/Drive-Smart-Blog/Drive-Smart-Ukraine/Ukraine-Road-Signs.aspx` \
This dataset provide 147 images of traffic signs accompanied with category labels (warning, mandatory, prohibitory)

Official traffic rule descriptions will be used for the textual description (300-360 rules): \
`https://pdr.infotech.gov.ua/theory/rules`

Each traffic sign is represented using:
- image (visual representation)
- textual description (meaning, usage)
metadata fields such as:
`sign_type`,
`category`,
`source`

Each traffic sign image is associated with its textual description via a shared sign ID stored in metadata.
Text-based retrieval is used to identify relevant signs, while the linked images are presented alongside the retrieved descriptions to provide visual context.
### Example Queries
The assistant may help with both general questions and signs-related quaries:
1. What does a driver need to do at a pedestrian crossing?
2. What are the rules for driving through an uncontrolled intersection?
3. When is it allowed to overtake another vehicle?
4. Which traffic signs warn about dangerous road conditions?
5. Show examples of warning signs and explain their purpose
6. What does a "No entry" sign look like and where is it used?
7. Show an example of a speed limit sign and explain when it applie
8. Which signs indicate a mandatory direction?


### Success Metrics
- **Retrieval accuracy:** Top-3 retrieval should contain correct source for ≥70% of test queries
- **Image-text consistency:** Manual verification should show ≥80% alignment
- **Answer Correctness:** ≥75% of answers should be factually correct and well-cited
- **Latency:** < 5 seconds per query end-to-end


### UI Expectations
The UI will be simple and intuituve for user, it will contain:
- user's quary
- textual explanation
- one or more related images

### Technical choices (initial)
**LLM**: Gemini 2.0 Flash \
**Embeddings**: Vertex AI Multimodal Embeddings API (text + image in a shared embedding space)\
**Vector store**: Vertex AI Vector Search.
