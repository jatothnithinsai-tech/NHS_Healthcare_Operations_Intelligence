import hashlib
from unittest.mock import Mock
import pytest
from src.ingestion import acquire


def test_official_host_enforced():
    with pytest.raises(ValueError,match='host'):
        acquire.download_one({'url':'https://unofficial.example/data.csv'})


def test_local_checksum_detects_corruption(tmp_path,monkeypatch):
    monkeypatch.setattr(acquire,'ROOT',tmp_path)
    (tmp_path/'x.csv').write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='corrupt'):
        acquire.download_one({'url':'https://www.england.nhs.uk/x.csv'},{'local_path':'x.csv','sha256':'0'*64},False)


def test_revision_preserves_old_file(tmp_path,monkeypatch):
    monkeypatch.setattr(acquire,'ROOT',tmp_path)
    prior=tmp_path/'old.csv'
    prior.write_bytes(b'prior')
    old={'sha256':hashlib.sha256(b'prior').hexdigest(),'url':'https://www.england.nhs.uk/old.csv','local_path':'old.csv'}
    response=Mock(status_code=200,content=b'Period,Count\nTEST,2\n',headers={})
    mocked=Mock()
    mocked.get.return_value=response
    monkeypatch.setattr(acquire,'session',lambda:mocked)
    source={'url':'https://www.england.nhs.uk/new.csv','dataset':'ae','reporting_month':'2026-01-01'}
    result=acquire.download_one(source,old,True)
    assert result['download_status']=='revised'
    assert result['supersedes_sha256']==old['sha256']
    assert prior.read_bytes()==b'prior'
    assert (tmp_path/result['local_path']).exists()


def test_html_error_not_loaded_as_csv(tmp_path,monkeypatch):
    monkeypatch.setattr(acquire,'ROOT',tmp_path)
    response=Mock(status_code=200,content=b'<html>verification</html>',headers={})
    mocked=Mock()
    mocked.get.return_value=response
    monkeypatch.setattr(acquire,'session',lambda:mocked)
    with pytest.raises(ValueError,match='payload'):
        acquire.download_one({'url':'https://www.england.nhs.uk/data.csv','dataset':'ae','reporting_month':'2026-01-01'})


def test_download_failure_propagates(monkeypatch):
    mocked=Mock()
    mocked.get.side_effect=TimeoutError('Synthetic controlled network timeout')
    monkeypatch.setattr(acquire,'session',lambda:mocked)
    with pytest.raises(TimeoutError):
        acquire.download_one({'url':'https://www.england.nhs.uk/data.csv'})
