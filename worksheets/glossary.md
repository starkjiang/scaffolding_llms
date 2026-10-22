# Glossary

Print this. It is the same list as the slide, with a little more room.

| Term | What it actually means | Everyday equivalent |
|---|---|---|
| **LLM** | The model itself: it predicts the next piece of text, very well | A brilliant, forgetful new hire |
| **Next-token prediction** | The one mechanism underneath everything an LLM does | Guessing the next word, very fast, forever |
| **Inference** | One run of the model to produce an answer | Asking the question once |
| **Prompt** | The instructions and material you send the model in one request | The task you write out for a new hire |
| **System prompt** | The standing instructions that go with every request | The job description, as opposed to today's task |
| **Context window** | How much text the model can hold in mind at once | What fits on the desk in front of them |
| **Token** | A chunk of text, roughly ¾ of a word; the unit you are billed in | Words on the page you pay for |
| **Few-shot** | Showing two or three worked examples inside the prompt | "Here, like this one" |
| **Chain-of-thought** | Asking it to work through the steps before answering | Show your working |
| **Structured output** | Requiring a fixed set of fields, usually JSON | A form instead of an essay |
| **Refusal rule** | The instruction for what to do when it does not know | "Write 'not stated' — never guess" |
| **Stateless** | It keeps nothing between conversations | They forget everything overnight |
| **Knowledge cutoff** | The date its training data stops | The last newspaper they read |
| **Context rot** | Quality dropping as the window fills, before the limit | Things buried mid-pile get missed |
| **Compaction** | Replacing old conversation with a running summary | Minutes instead of the full transcript |
| **Hallucination** | A confident, fluent, wrong answer | Bluffing in a meeting |
| **Grounding** | Making the model answer from supplied material rather than memory | Saying "use this file, not what you remember" |
| **RAG / retrieval** | Finding the right documents and putting them in the prompt | An open-book exam |
| **Chunk** | One piece of a document, as stored for searching | A page or section |
| **Embedding** | A numerical representation of meaning, used for search | Filing by topic rather than by title |
| **Hybrid search** | Searching by meaning and by exact words together | Looking in the index *and* skimming the headings |
| **Recall@5** | How often the right section appears in the top five search results | Whether you opened the right page |
| **Tool / function call** | Letting the model ask your software to do something | Giving them a calculator and a database login |
| **MCP** | A common standard for connecting models to tools | A standard plug instead of a custom adapter per device |
| **Agent** | A model that chooses its own next step, in a loop | An intern working unsupervised |
| **Orchestration** | Deciding the order the steps run in | The workflow or the process map |
| **Guardrail** | An automatic check that blocks a bad input or output | The approval step before something ships |
| **Human in the loop** | A required person's decision before an action happens | A signature |
| **Evaluation / eval** | A fixed set of test cases you score the system against | A marked exam re-run after every change |
| **Model-as-judge** | Using a second AI request to grade the first one's answer | A colleague marking to a rubric |
| **Trace** | The record of every step taken for one request | The audit trail |
| **Temperature** | How much randomness is allowed in the answer | How much creative licence you grant |
| **Model tier** | Which size of model you use for a step | Who you assign a task to: junior or senior |
| **Prompt injection** | Instructions hidden in content the model reads | A forged note slipped into the in-tray |
| **Fine-tuning** | Further training a model on your own examples | Sending someone on a course — expensive, and rarely the first answer |
