from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from consolidate_neshov_paperlike_fmd import validate_panel


def test_rejects_any_missing_or_duplicate_paperlike_fold():
    parts=[{'dataset':'FMD','repetition':r,'outer_fold':f,'seed':42*r,'training_seed':42*r,
            'training_indices':list(range(900)), 'external_indices':list(range(f*100,(f+1)*100))}
           for r in range(1,11) for f in range(10)]
    validate_panel(parts)
    with pytest.raises(ValueError): validate_panel(parts[:-1])
    with pytest.raises(ValueError): validate_panel(parts[:-1]+[parts[0]])
