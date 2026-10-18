"""Strict native reviewer frame; JSON escaping belongs to the transport."""
import re

from notifications import JSON_INSTRUCTION as _JSON_INSTRUCTION
_UUID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')

def frame_prompt(base, batch_id):
    if not _UUID.fullmatch(batch_id) or _JSON_INSTRUCTION not in base:
        raise ValueError('Invalid reviewer prompt contract')
    instructions = (
        'Return one BKRV1 frame, not JSON or a code fence. Copy this exact structure, '
        'using literal text (do not JSON-escape quotes or backslashes):\n'
        f'BKRV1 {batch_id}\nMEMORY\nShort factual summary\nREPLY TEXT\nUseful answer\nEND {batch_id}\n'
        'For a null reply replace REPLY TEXT and its answer with the single line REPLY NONE. '
        'Do not output extra framing or text outside the frame. Never include a control line '
        '(MEMORY, REPLY TEXT, REPLY NONE, BKRV1 or END followed by a receipt) inside a field. '
    )
    return base.replace(_JSON_INSTRUCTION, instructions, 1)

def parse_frame(raw, batch_id):
    if not _UUID.fullmatch(batch_id) or not isinstance(raw,str) or len(raw)>24000:
        raise ValueError('Invalid reviewer frame')
    # Newlines at the outer boundary are harmless; prose, fences and duplicate
    # frames are not. No recovery of malformed JSON and no missing receipt synthesis.
    lines=raw.strip('\r\n').splitlines()
    if len(lines)<5 or lines[0]!=f'BKRV1 {batch_id}' or lines[-1]!=f'END {batch_id}' or lines[1]!='MEMORY':
        raise ValueError('Missing matching reviewer frame boundaries')
    controls=[i for i,line in enumerate(lines[2:-1],2) if line in ('REPLY NONE','REPLY TEXT')]
    if len(controls)!=1:
        raise ValueError('Missing or duplicate reviewer reply control')
    pivot=controls[0]; memory='\n'.join(lines[2:pivot])
    body=lines[pivot+1:-1]
    for line in lines[2:pivot]+body:
        if line=='MEMORY' or line.startswith(('BKRV1 ','END ','REPLY ')):
            raise ValueError('Reserved control line inside reviewer field')
    if not memory.strip() or len(memory)>2000:
        raise ValueError('Invalid reviewer memory')
    if lines[pivot]=='REPLY NONE':
        if body:raise ValueError('Unexpected text in null reply')
        reply=None
    else:
        reply='\n'.join(body)
        if not reply.strip() or len(reply)>12000:raise ValueError('Invalid reviewer reply')
    return {'receipt':batch_id,'memory':memory,'reply':reply}
