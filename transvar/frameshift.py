from transcripts import *
from utils import *
from record import *
from err import *

def _annotate_frameshift(args, q, t):

    if q.alt and q.alt not in reverse_codon_table:
        err_warn('unknown alternative: %s, ignore alternative' % q.alt)
        q.alt = ''

    # when there's a transcript specification
    if q.tpt and t.name != q.tpt:
        raise IncompatibleTranscriptError('transcript id unmatched')

    t.ensure_seq()

    if (q.pos <= 0 or q.pos > t.cdslen()):
        raise IncompatibleTranscriptError('codon nonexistent')
    codon = t.cpos2codon(q.pos)
    if not codon:
        raise IncompatibleTranscriptError('codon nonexistent')

    # skip if reference amino acid is given
    # and codon sequence does not generate reference aa
    # codon.seq is natural sequence
    if q.ref and codon.seq not in aa2codon(q.ref):
        raise IncompatibleTranscriptError('reference amino acid unmatched')

    r = Record()
    r.chrm = t.chrm
    r.tname = t.format()
    r.gene = t.gene.name
    r.strand = t.strand
    r.pos = '-'.join(map(str, codon.locs))
    tnuc_beg = (codon.index-1)*3+1
    tnuc_end = (q.pos+q.stop_index)*3 # may be out of bound
    r.tnuc_range = '%d-%d' % (tnuc_beg, tnuc_end)
    if tnuc_end >= t.cdslen():
        t.ensure_position_array()
        gnuc_beg = t.tnuc2gnuc(tnuc_beg)
        gnuc_end = t.cds_end + tnuc_end - t.cdslen()
    else:
        gnuc_beg, gnuc_end = t.tnuc_range2gnuc_range(tnuc_beg, tnuc_end)
    r.gnuc_range = '%d-%d' % (gnuc_beg, gnuc_end)
    r.append_info('imprecise')

    return r


def annotate_frameshift(args, q, tpts, db):

    found = False
    rs = []
    for t in tpts:
        try:
            r = _annotate_frameshift(args, q, t)
        except IncompatibleTranscriptError:
            continue
        except UnknownChromosomeError:
            continue
        r.taa_range = '%s%d%sfs*%d' % (aaf(q.ref, args), q.pos, aaf(q.alt, args), q.stop_index)
        r.reg = RegCDSAnno(t)
        r.reg.from_taa_range(q.pos, q.pos+q.stop_index)
        r.format(q.op)
        found = True
        format_one(r, rs, q, args)
    format_all(rs, q, args)

    if not found:
        r = Record()
        r.taa_range = '%s%d%sfs*%d' % (aaf(q.ref, args), q.pos, aaf(q.alt, args), q.stop_index)
        r.append_info('no_valid_transcript_found_(from_%s_candidates)' % len(tpts))
        r.format(q.op)

