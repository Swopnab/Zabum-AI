"""Conservative lexical evidence gate, not an entailment or answer-accuracy model."""
import re
STOP_WORDS=set('the a an is are was were what how do does did my your in of to and about say documents uploaded when where which who why please tell me from for that this can you it'.split())
def supported_passages(query, sources):
    terms=set(re.findall(r'\w+',query.lower()))-STOP_WORDS
    # Require every remaining query term in one passage. Prefer abstention to filling gaps.
    return [source for source in sources if terms and terms.issubset(set(re.findall(r'\w+',source.get('content_preview',source.get('content','')).lower())))]
