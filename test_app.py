import os
import tempfile
import pytest
from main import app, db, validate_and_calculate_csv

@pytest.fixture
def client():
    db_fd,db_path = tempfile.mkstemp()
    app.config['SQLALCHEMY_DATABASE_URI'] =f'sqlite:///{db_path}'
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        with app.app_context:
            db.create_all()
        yield client
    os.close(db_fd)
    os.unlink(db_path)


def test_validate_and_calculate_csv():
    valid_csv = 'A|O|B\n1|+|1\n2|-|1\n3|*|2\n4|/|2'
    with tempfile.NamedTemporaryFile(delete=False, mode='w', newline='') as tmpfile:
        tmpfile.write(valid_csv)
        tmp_file_path = tmpfile.name
    try:
        result = validate_and_calculate_csv(tmp_file_path)
        assert result == 11.0 #Expected result
    finally:
        os.remove(tmp_file_path)
        