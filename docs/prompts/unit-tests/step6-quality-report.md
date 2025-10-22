> You are a senior software engineer specializing in writing maintainable, scalable, behavior-driven tests. First, read `@docs/guides/testing/WRITING_TESTS.md`,  
`@docs/guides/testing/UNIT_TESTS.md `. and `@docs/guides/testing/INTEGRATION_TESTS.md`. Then summarize the 3 most important principles and the 3 most important anti-patterns 
from the documents.

Next, please comprehensively review the `text_processor` unit test suite for the component defined by the public contract at `backend/contracts/services/text_processor.pyi` 
located at `backend/tests/unit/text_processor`. Create a quality report at `backend/tests/unit/text_processor/QUALITY_REPORT.md` that evaluates the test suite and its 
implementation. In the report, specifically asssess whether any of the unit tests should be transformed into integration tests instead as they more properly test interactions 
between backend system components. 