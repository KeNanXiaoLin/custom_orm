from typing import List, Optional, TypeVar, Type, Any, Dict
from .models import Model
from .db import Database


ModelType = TypeVar('ModelType', bound='Model')


class Query:
    def __init__(self, model_class: Type[ModelType], db: Database):
        self.model_class = model_class
        self.db = db
        self._filters: List[str] = []
        self._filter_params: List[Any] = []
        self._order_by: Optional[str] = None
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
    
    def _clone(self) -> 'Query':
        """Create a copy of this query object"""
        query = Query(self.model_class, self.db)
        query._filters = self._filters.copy()
        query._filter_params = self._filter_params.copy()
        query._order_by = self._order_by
        query._limit = self._limit
        query._offset = self._offset
        return query
    
    def filter(self, *conditions: str) -> 'Query':
        """Add filter conditions using SQL syntax"""
        query = self._clone()
        query._filters.extend(conditions)
        return query
    
    def filter_by(self, **kwargs) -> 'Query':
        """Add filter conditions by attribute values"""
        query = self._clone()
        for attr_name, value in kwargs.items():
            field = self.model_class.__fields__.get(attr_name)
            if not field:
                raise ValueError(f"{self.model_class.__name__} has no field named {attr_name}")
            query._filters.append(f"{field.name} = ?")
            query._filter_params.append(value)
        return query
    
    def order_by(self, field_name: str, ascending: bool = True) -> 'Query':
        """Add order by clause"""
        query = self._clone()
        field = self.model_class.__fields__.get(field_name)
        if not field:
            raise ValueError(f"{self.model_class.__name__} has no field named {field_name}")
        direction = "ASC" if ascending else "DESC"
        query._order_by = f"{field.name} {direction}"
        return query
    
    def limit(self, limit: int) -> 'Query':
        """Add limit clause"""
        query = self._clone()
        query._limit = limit
        return query
    
    def offset(self, offset: int) -> 'Query':
        """Add offset clause"""
        query = self._clone()
        query._offset = offset
        return query
    
    def _build_sql(self) -> tuple[str, tuple]:
        """Build the SQL query and return it along with parameters"""
        fields = [field.name for field in self.model_class.__fields__.values()]
        select_sql = f"SELECT {', '.join(fields)} FROM {self.model_class.__table__}"
        
        sql_parts = [select_sql]
        
        if self._filters:
            where_sql = f"WHERE {' AND '.join(self._filters)}"
            sql_parts.append(where_sql)
        
        if self._order_by:
            sql_parts.append(f"ORDER BY {self._order_by}")
        
        # SQLite requires LIMIT before OFFSET
        if self._limit is not None:
            sql_parts.append(f"LIMIT {self._limit}")
        
        if self._offset is not None:
            # If LIMIT is not specified but OFFSET is, we need to provide a default LIMIT
            if self._limit is None:
                sql_parts.append("LIMIT -1")  # LIMIT -1 means no limit
            sql_parts.append(f"OFFSET {self._offset}")
        
        return ' '.join(sql_parts), tuple(self._filter_params)
    
    def all(self) -> List[ModelType]:
        """Return all results"""
        sql, params = self._build_sql()
        rows = self.db.fetch_all(sql, params)
        return [self._row_to_model(row) for row in rows]
    
    def first(self) -> Optional[ModelType]:
        """Return the first result"""
        query = self._clone()
        query._limit = 1
        sql, params = query._build_sql()
        row = self.db.fetch_one(sql, params)
        if row:
            return self._row_to_model(row)
        return None
    
    def _row_to_model(self, row: Dict[str, Any]) -> ModelType:
        """Convert a database row to a model instance"""
        model_kwargs = {}
        for field_name, field in self.model_class.__fields__.items():
            if field.name in row:
                model_kwargs[field_name] = row[field.name]
        return self.model_class(**model_kwargs)
    
    def count(self) -> int:
        """Return the number of results"""
        sql = f"SELECT COUNT(*) FROM {self.model_class.__table__}"
        params = tuple(self._filter_params)
        
        if self._filters:
            sql += f" WHERE {' AND '.join(self._filters)}"
        
        row = self.db.fetch_one(sql, params)
        return row['COUNT(*)'] if row else 0
    
    def exists(self) -> bool:
        """Return True if any results exist"""
        return self.count() > 0
    
    # Dynamic method generation for common queries
    def __getattr__(self, name: str) -> Any:
        """Handle dynamic method calls like get_by_name()"""
        if name.startswith('filter_by_'):
            field_name = name[10:]
            
            def dynamic_filter(**kwargs):
                if field_name not in kwargs:
                    raise ValueError(f"Missing required parameter {field_name}")
                return self.filter_by(**{field_name: kwargs[field_name]})
            
            return dynamic_filter
        raise AttributeError(f"{self.__class__.__name__} object has no attribute {name}")
