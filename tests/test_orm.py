import unittest
import os
from orm import (
    Model, IntegerField, StringField, BooleanField, DateTimeField, FloatField,
    Database
)


from orm.models import model_fields


@model_fields
class TestModel(Model):
    __table__ = 'test_models'
    id = IntegerField(primary_key=True)
    name = StringField(max_length=100, nullable=False)
    description = StringField(max_length=500, nullable=True)
    active = BooleanField(default=True)
    price = FloatField(default=0.0)


class TestORM(unittest.TestCase):
    db_path = 'test.db'
    
    def setUp(self):
        # Clean up any existing test database
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        
        # Create a new database and table
        with Database(self.db_path) as db:
            TestModel.create_table(db)
    
    def tearDown(self):
        # Clean up test database
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_field_validation(self):
        # Test StringField validation
        with self.assertRaises(ValueError):
            TestModel(name=123)
        
        with self.assertRaises(ValueError):
            TestModel(name='a' * 101)
        
        # Test IntegerField validation
        with self.assertRaises(ValueError):
            TestModel(name='test', id='not-an-int')
        
        # Test BooleanField validation
        with self.assertRaises(ValueError):
            TestModel(name='test', active='not-a-bool')
        
        # Test FloatField validation
        with self.assertRaises(ValueError):
            TestModel(name='test', price='not-a-float')
    
    def test_model_creation(self):
        # Test model instantiation with default values
        model = TestModel(name='Test Item')
        self.assertEqual(model.name, 'Test Item')
        self.assertIsNone(model.description)
        self.assertTrue(model.active)
        self.assertEqual(model.price, 0.0)
        self.assertIsNone(model.id)
    
    def test_save_and_get(self):
        # Test saving a new model
        model = TestModel(name='Test Item', description='Test Description', price=10.99)
        with Database(self.db_path) as db:
            model.save(db)
        
        # Test retrieving the model
        with Database(self.db_path) as db:
            retrieved = TestModel.get(db, model.id)
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, model.id)
        self.assertEqual(retrieved.name, model.name)
        self.assertEqual(retrieved.description, model.description)
        self.assertEqual(retrieved.price, model.price)
    
    def test_update(self):
        # Create and save a model
        model = TestModel(name='Test Item')
        with Database(self.db_path) as db:
            model.save(db)
        
        # Update the model
        model.name = 'Updated Item'
        model.price = 19.99
        with Database(self.db_path) as db:
            model.save(db)
        
        # Retrieve and verify the update
        with Database(self.db_path) as db:
            retrieved = TestModel.get(db, model.id)
        
        self.assertEqual(retrieved.name, 'Updated Item')
        self.assertEqual(retrieved.price, 19.99)
    
    def test_delete(self):
        # Create and save a model
        model = TestModel(name='Test Item')
        with Database(self.db_path) as db:
            model.save(db)
            model_id = model.id
        
        # Delete the model
        with Database(self.db_path) as db:
            model.delete(db)
        
        # Verify deletion
        with Database(self.db_path) as db:
            retrieved = TestModel.get(db, model_id)
        
        self.assertIsNone(retrieved)
    
    def test_query_all(self):
        # Create multiple models
        models = [
            TestModel(name='Item 1'),
            TestModel(name='Item 2'),
            TestModel(name='Item 3')
        ]
        
        with Database(self.db_path) as db:
            for model in models:
                model.save(db)
        
        # Query all models
        with Database(self.db_path) as db:
            all_models = TestModel.select(db).all()
        
        self.assertEqual(len(all_models), 3)
    
    def test_query_filter_by(self):
        # Create multiple models
        models = [
            TestModel(name='Item 1', active=True),
            TestModel(name='Item 2', active=False),
            TestModel(name='Item 3', active=True)
        ]
        
        with Database(self.db_path) as db:
            for model in models:
                model.save(db)
        
        # Test filter_by
        with Database(self.db_path) as db:
            active_models = TestModel.select(db).filter_by(active=True).all()
            self.assertEqual(len(active_models), 2)
            
            # Test filter_by method instead of dynamic get_by_name
            item_2 = TestModel.select(db).filter_by(name='Item 2').first()
            self.assertIsNotNone(item_2)
            self.assertEqual(item_2.name, 'Item 2')
    
    def test_query_order_by(self):
        # Create multiple models
        models = [
            TestModel(name='Item C', price=30.0),
            TestModel(name='Item A', price=10.0),
            TestModel(name='Item B', price=20.0)
        ]
        
        with Database(self.db_path) as db:
            for model in models:
                model.save(db)
        
        # Test ascending order
        with Database(self.db_path) as db:
            sorted_models = TestModel.select(db).order_by('name').all()
            self.assertEqual([m.name for m in sorted_models], ['Item A', 'Item B', 'Item C'])
        
        # Test descending order
        with Database(self.db_path) as db:
            sorted_models = TestModel.select(db).order_by('price', ascending=False).all()
            self.assertEqual([m.price for m in sorted_models], [30.0, 20.0, 10.0])
    
    def test_query_limit_offset(self):
        # Create multiple models
        for i in range(5):
            model = TestModel(name=f'Item {i}', price=float(i))
            with Database(self.db_path) as db:
                model.save(db)
        
        # Test limit
        with Database(self.db_path) as db:
            limited_models = TestModel.select(db).limit(2).all()
            self.assertEqual(len(limited_models), 2)
        
        # Test offset
        with Database(self.db_path) as db:
            offset_models = TestModel.select(db).offset(2).all()
            self.assertEqual(len(offset_models), 3)
        
        # Test limit and offset together
        with Database(self.db_path) as db:
            paginated_models = TestModel.select(db).limit(2).offset(1).all()
            self.assertEqual(len(paginated_models), 2)
            self.assertEqual([m.name for m in paginated_models], ['Item 1', 'Item 2'])
    
    def test_query_count(self):
        # Create multiple models
        for i in range(3):
            model = TestModel(name=f'Item {i}')
            with Database(self.db_path) as db:
                model.save(db)
        
        # Test count
        with Database(self.db_path) as db:
            total_count = TestModel.select(db).count()
            self.assertEqual(total_count, 3)
            
            # Test count with filter
            active_count = TestModel.select(db).filter_by(active=True).count()
            self.assertEqual(active_count, 3)
    
    def test_exists(self):
        # Create a model
        model = TestModel(name='Test Item')
        with Database(self.db_path) as db:
            model.save(db)
        
        # Test exists
        with Database(self.db_path) as db:
            self.assertTrue(TestModel.select(db).filter_by(name='Test Item').exists())
            self.assertFalse(TestModel.select(db).filter_by(name='Non-existent Item').exists())


if __name__ == '__main__':
    unittest.main()
