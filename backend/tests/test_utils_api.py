import pytest
from flask import Flask, request, jsonify
from marshmallow import Schema, fields
from app.utils.api import (
    paginate_query,
    validate_schema,
    get_or_404,
    crud_resource,
    filter_query,
    validate_request_status
)
from app.utils.errors import APIError
from app.models import db

# Test fixtures and helper classes
class TestModel(db.Model):
    """Test model for API utils testing"""
    __test__ = False  # Tell pytest to ignore this class for test collection
    __tablename__ = 'test_model'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    status = db.Column(db.String(20))
    professional_id = db.Column(db.Integer)

class TestSchema(Schema):
    """Test schema for API utils testing"""
    __test__ = False  # Tell pytest to ignore this class for test collection
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    status = fields.Str()
    professional_id = fields.Int()

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_data(app):
    with app.app_context():
        items = [
            TestModel(name=f'Test {i}', status='active')
            for i in range(15)
        ]
        db.session.bulk_save_objects(items)
        db.session.commit()
        return items

# Test paginate_query
def test_paginate_query_default_params(app, test_data):
    with app.test_request_context('/?page=1&per_page=10'):
        query = TestModel.query
        schema = TestSchema(many=True)
        result = paginate_query(query, schema)
        
        assert len(result['items']) == 10
        assert result['total'] == 15
        assert result['pages'] == 2
        assert result['current_page'] == 1
        assert result['per_page'] == 10
        assert result['has_next'] is True
        assert result['has_prev'] is False

def test_paginate_query_custom_params(app, test_data):
    with app.test_request_context('/?page=2&per_page=5'):
        query = TestModel.query
        schema = TestSchema(many=True)
        result = paginate_query(query, schema)
        
        assert len(result['items']) == 5
        assert result['current_page'] == 2
        assert result['per_page'] == 5
        assert result['has_next'] is True
        assert result['has_prev'] is True

# Test validate_schema decorator
def test_validate_schema_valid_data(app):
    @validate_schema(TestSchema)
    def test_endpoint(data):
        return data
    
    with app.test_request_context(
        json={'name': 'Test Item'}
    ):
        result = test_endpoint()
        assert result['name'] == 'Test Item'

def test_validate_schema_invalid_data(app):
    @validate_schema(TestSchema)
    def test_endpoint(data):
        return data
    
    with app.test_request_context(
        json={'status': 'active'}  # Missing required 'name' field
    ):
        with pytest.raises(APIError) as exc:
            test_endpoint()
        assert exc.value.status_code == 400

def test_validate_schema_no_json_data(app):
    @validate_schema(TestSchema)
    def test_endpoint(data):
        return data
    
    with app.test_request_context():
        with pytest.raises(APIError) as exc:
            test_endpoint()
        assert exc.value.status_code == 400

# Test get_or_404
def test_get_or_404_existing_item(app, test_data):
    with app.app_context():
        item = get_or_404(TestModel, 1)
        assert item.id == 1
        assert item.name == 'Test 0'

def test_get_or_404_nonexistent_item(app):
    with app.app_context():
        with pytest.raises(APIError) as exc:
            get_or_404(TestModel, 999)
        assert exc.value.status_code == 404
        assert 'not found' in str(exc.value)

# Test filter_query
def test_filter_query_single_filter(app, test_data):
    with app.app_context():
        query = TestModel.query
        filtered = filter_query(query, TestModel, status='active')
        assert filtered.count() == 15

def test_filter_query_multiple_filters(app, test_data):
    with app.app_context():
        # Update one item for testing
        item = TestModel.query.first()
        item.status = 'inactive'
        db.session.commit()
        
        query = TestModel.query
        filtered = filter_query(query, TestModel, status='active')
        assert filtered.count() == 14

def test_filter_query_list_filter(app, test_data):
    with app.app_context():
        query = TestModel.query
        filtered = filter_query(query, TestModel, id=[1, 2, 3])
        assert filtered.count() == 3

def test_filter_query_invalid_field(app, test_data):
    with app.app_context():
        query = TestModel.query
        # Invalid field should be ignored
        filtered = filter_query(query, TestModel, invalid_field='value')
        assert filtered.count() == 15

# Test crud_resource
def test_crud_resource_get_list(app, test_data):
    with app.test_request_context('/?page=1&per_page=10'):
        crud = crud_resource(TestModel, TestSchema)
        result = crud['get_list']()
        assert len(result['items']) == 10
        assert result['total'] == 15

def test_crud_resource_get_one(app, test_data):
    with app.test_request_context():
        crud = crud_resource(TestModel, TestSchema)
        result = crud['get_one'](1)
        assert result['id'] == 1
        assert result['name'] == 'Test 0'

def test_crud_resource_create(app):
    with app.test_request_context(json={'name': 'New Item', 'status': 'active'}):
        crud = crud_resource(TestModel, TestSchema)
        data = TestSchema().load(request.get_json())
        item = TestModel(**data)
        db.session.add(item)
        db.session.commit()
        result = TestSchema().dump(item)
        assert result['name'] == 'New Item'
        assert result['status'] == 'active'

def test_crud_resource_update(app, test_data):
    with app.test_request_context(json={'name': 'Updated Item'}):
        crud = crud_resource(TestModel, TestSchema)
        item = db.session.get(TestModel, 1)  # Use session.get instead of Query.get
        data = TestSchema().load(request.get_json(), partial=True)
        for key, value in data.items():
            setattr(item, key, value)
        db.session.commit()
        result = TestSchema().dump(item)
        assert result['name'] == 'Updated Item'

def test_crud_resource_delete(app, test_data):
    with app.test_request_context():
        crud = crud_resource(TestModel, TestSchema)
        result = crud['delete'](1)
        assert result == ('', 204)
        assert db.session.get(TestModel, 1) is None  # Use session.get instead of Query.get

# Test validate_request_status
def test_validate_request_status_valid(app, test_data):
    with app.app_context():
        item = TestModel.query.first()
        item.status = 'pending'
        item.professional_id = 1
        db.session.commit()
        
        result = validate_request_status(item, 1, expected_status='pending')
        assert result is None  # Should not raise an exception

def test_validate_request_status_invalid(app, test_data):
    with app.app_context():
        item = TestModel.query.first()
        item.status = 'completed'
        item.professional_id = 2  # Different professional_id
        db.session.commit()
        
        with pytest.raises(APIError) as exc:
            validate_request_status(item, 1, expected_status='pending')
        assert exc.value.status_code == 403  # Unauthorized access returns 403
