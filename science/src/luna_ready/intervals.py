"""Sampled state intervals with transition brackets and edge censoring."""
from datetime import datetime


def sampled_intervals(times,states,wanted=True):
    if len(times)!=len(states) or not times:raise ValueError('Nonempty aligned series required')
    parsed=[datetime.fromisoformat(t.replace('Z','+00:00')) for t in times]
    if any(b<=a for a,b in zip(parsed,parsed[1:])):raise ValueError('Times must increase')
    out=[];i=0
    while i<len(states):
        if states[i] is not wanted:i+=1;continue
        start=i
        while i+1<len(states) and states[i+1] is wanted:i+=1
        end=i
        left_unknown=start>0 and states[start-1] is None
        right_unknown=end+1<len(states) and states[end+1] is None
        out.append(dict(first_sample_utc=times[start],last_sample_utc=times[end],
            sample_span_hours=(parsed[end]-parsed[start]).total_seconds()/3600,
            start_transition_bracket_utc=None if start==0 or left_unknown else [times[start-1],times[start]],
            end_transition_bracket_utc=None if end==len(states)-1 or right_unknown else [times[end],times[end+1]],
            left_censored=start==0 or left_unknown,right_censored=end==len(states)-1 or right_unknown,
            interpretation='Sampled run; between-sample reversals are not excluded; sample span is not exact event duration'))
        i+=1
    return out
