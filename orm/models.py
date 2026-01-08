import datetime
from typing import Dict, Any, List, Optional, TypeVar, Type
from .fields import Field
from .db import Database


ModelType = TypeVar('ModelType', bound='Model')


class Model:
    __table__: str
    __fields__: Dict[str, Field] = {}
    __primary_key__: Optional[Field] = None
    
    def __init__(self, **kwargs):
        # Initialize all fields with default values
        for field_name, field in self.__class__.__fields__.items():
            setattr(self, field_name, kwargs.pop(field_name, field.default))
        
        if kwargs:
            raise TypeError(f"Unexpected keyword arguments: {list(kwargs.keys())}")
    
    def __repr__(self):
        primary_key_field = self.__class__.__primary_key__
        if primary_key_field:
            primary_key_value = getattr(self, primary_key_field._attr_name, None)
            if primary_key_value is not None:
                return f"<{self.__class__.__name__} {primary_key_field._attr_name}={primary_key_value}>"
        return f"<{self.__class__.__name__} (unsaved)>"
    
    @classmethod
    def get_table_name(cls) -> str:
        return cls.__table__
    
    @classmethod
    def get_primary_key(cls) -> Optional[Field]:
        return cls.__primary_key__
    
    @classmethod
    def get_fields(cls) -> Dict[str, Field]:
        return cls.__fields__.copy()
    
    @classmethod
    def create_table(cls, db: Database):
        fields_sql = []
        for field in cls.__fields__.values():
            field_sql = f"{field.name} {field.db_type()}"
            if field.primary_key:
                field_sql += " PRIMARY KEY"
            if not field.nullable:
                field_sql += " NOT NULL"
            if field.default is not None:
                if isinstance(field.default, str):
                    field_sql += f" DEFAULT '{field.default}'"
                else:
                    field_sql += f" DEFAULT {field.default}"
            fields_sql.append(field_sql)
        
        create_sql = f"CREATE TABLE IF NOT EXISTS {cls.__table__} ({', '.join(fields_sql)})"
        db.execute(create_sql)
        db.commit()
    
    @classmethod
    def drop_table(cls, db: Database):
        drop_sql = f"DROP TABLE IF EXISTS {cls.__table__}"
        db.execute(drop_sql)
    
    @classmethod
    def select(cls, db: Database) -> 'Query':
        from .query import Query
        return Query(cls, db)
    
    @classmethod
    def get(cls, db: Database, id: Any) -> Optional[ModelType]:
        if not cls.__primary_key__:
            raise ValueError(f"{cls.__name__} has no primary key")
        
        query = cls.select(db).filter_by(**{cls.__primary_key__._attr_name: id})
        return query.first()
    
    def save(self, db: Database) -> None:
        if self.__class__.__primary_key__:
            pk_value = getattr(self, self.__class__.__primary_key__._attr_name)
            if pk_value is None:
                self._insert(db)
            else:
                self._update(db)
        else:
            self._insert(db)
    
    def _insert(self, db: Database) -> None:
        # Include all fields except auto-increment primary key
        fields = []
        for field in self.__class__.__fields__.values():
            if field.primary_key:
                # Skip auto-increment primary keys that have no value yet
                if getattr(self, field._attr_name) is None:
                    continue
            fields.append(field)
        
        field_names = [field.name for field in fields]
        values = [getattr(self, field._attr_name) for field in fields]
        
        placeholders = ', '.join(['?'] * len(fields))
        insert_sql = f"INSERT INTO {self.__class__.__table__} ({', '.join(field_names)}) VALUES ({placeholders})"
        
        cursor = db.execute(insert_sql, tuple(values))
        
        # Set auto-increment primary key value if applicable
        if self.__class__.__primary_key__ and getattr(self, self.__class__.__primary_key__._attr_name) is None:
            setattr(self, self.__class__.__primary_key__._attr_name, cursor.lastrowid)
    
    def _update(self, db: Database) -> None:
        if not self.__class__.__primary_key__:
            raise ValueError(f"{self.__class__.__name__} has no primary key")
        
        update_fields = [field for field in self.__class__.__fields__.values() if not field.primary_key]
        update_set = ', '.join([f"{field.name} = ?" for field in update_fields])
        values = [getattr(self, field._attr_name) for field in update_fields]
        
        pk_name = self.__class__.__primary_key__.name
        pk_value = getattr(self, self.__class__.__primary_key__._attr_name)
        
        update_sql = f"UPDATE {self.__class__.__table__} SET {update_set} WHERE {pk_name} = ?"
        db.execute(update_sql, tuple(values) + (pk_value,))
    
    def delete(self, db: Database) -> None:
        if not self.__class__.__primary_key__:
            raise ValueError(f"{self.__class__.__name__} has no primary key")
        
        pk_name = self.__class__.__primary_key__.name
        pk_value = getattr(self, self.__class__.__primary_key__._attr_name)
        
        delete_sql = f"DELETE FROM {self.__class__.__table__} WHERE {pk_name} = ?"
        db.execute(delete_sql, (pk_value,))
        
        # Reset primary key value
        setattr(self, self.__class__.__primary_key__._attr_name, None)
    
    def to_dict(self) -> Dict[str, Any]:
        return {field_name: getattr(self, field_name) for field_name in self.__class__.__fields__}


# Add this decorator to help with field collection
def model_fields(cls):
    """Decorator to collect fields and primary key for a model class"""
    # Collect all fields
    fields = {}
    primary_key = None
    
    # Iterate through class attributes
    for attr_name, attr in cls.__dict__.items():
        if isinstance(attr, Field):
            fields[attr_name] = attr
            if attr.primary_key:
                primary_key = attr
    
    # Set class attributes
    cls.__fields__ = fields
    cls.__primary_key__ = primary_key
    
    # Generate table name if not provided
    if not hasattr(cls, '__table__'):
        cls.__table__ = cls.__name__.lower() + 's'
    
    return cls
