# File: app/repositories/neo4j_repository.py
"""Neo4j database repository for graph operations"""
from typing import Optional, Dict, Any, List
from app.repositories.base import BaseRepository
from app.database import Neo4jDriver
import logging

logger = logging.getLogger(__name__)


class Neo4jRepository(BaseRepository):
    """Repository for Neo4j graph database operations"""
    
    def __init__(self, driver: Neo4jDriver):
        self.driver = driver
    
    def create(self, data: Dict[str, Any]) -> Any:
        """Generic create method (not used directly)"""
        raise NotImplementedError("Use specific create methods")
    
    def get(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get node by ID"""
        query = """
        MATCH (n {id: $id})
        OPTIONAL MATCH (n)-[r]->(target)
        RETURN n, collect({
            target_id: coalesce(target.id, elementId(target)), 
            type: type(r), 
            weight: coalesce(r.weight, 1.0)
        }) as relationships
        """
        with self.driver.get_session() as session:
            res = session.run(query, id=entity_id)
            record = res.single()
            if record:
                node_data = dict(record['n'])
                rels = [r for r in record['relationships'] if r['target_id'] is not None]
                node_data['relationships'] = rels
                return node_data
        return None
    
    def update(self, entity_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update node properties"""
        set_clauses = []
        params = {"id": entity_id}
        
        for key, value in data.items():
            if key not in ['id', 'relationships']:  # Skip reserved fields
                set_clauses.append(f"n.{key} = ${key}")
                params[key] = value
        
        if not set_clauses:
            return self.get(entity_id)
        
        query = f"MATCH (n {{id: $id}}) SET {', '.join(set_clauses)} RETURN n"
        with self.driver.get_session() as session:
            res = session.run(query, **params)
            record = res.single()
            if record:
                return dict(record['n'])
        return None
    
    def delete(self, entity_id: str) -> bool:
        """Delete node and all relationships"""
        query = "MATCH (n {id: $id}) DETACH DELETE n"
        with self.driver.get_session() as session:
            result = session.run(query, id=entity_id)
            summary = result.consume()
            return summary.counters.nodes_deleted > 0
    
    # Specific methods for document operations
    def create_document_node(self, doc_id: str, text: str, title: str, 
                            vector_id: int, lang: str, chunk_index: int,
                            metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create a document node in Neo4j"""
        query = """
        CREATE (d:Document {
            id: $id,
            text: $text,
            title: $title,
            vector_id: $vector_id,
            lang: $lang,
            chunk_index: $chunk_index
        })
        SET d += $metadata
        RETURN d
        """
        with self.driver.get_session() as session:
            result = session.run(
                query, 
                id=doc_id, 
                text=text, 
                title=title, 
                vector_id=vector_id,
                lang=lang,
                chunk_index=chunk_index,
                metadata=metadata
            )
            record = result.single()
            return dict(record['d']) if record else None
    
    def create_edge(self, source_id: str, target_id: str, edge_type: str, 
                   weight: float, metadata: Dict[str, Any]) -> Any:
        """Create a relationship between two nodes"""
        query = f"""
        MATCH (source {{id: $source_id}})
        MATCH (target {{id: $target_id}})
        MERGE (source)-[r:{edge_type}]->(target)
        SET r.weight = $weight
        SET r += $metadata
        RETURN r
        """
        with self.driver.get_session() as session:
            result = session.run(
                query, 
                source_id=source_id, 
                target_id=target_id, 
                weight=weight,
                metadata=metadata
            )
            record = result.single()
            return record['r'] if record else None
    
    def get_edge(self, edge_id: str) -> Optional[Dict[str, Any]]:
        """Get edge by element ID"""
        query = "MATCH ()-[r]-() WHERE elementId(r) = $id RETURN r"
        with self.driver.get_session() as session:
            res = session.run(query, id=edge_id)
            record = res.single()
            if record:
                r = record['r']
                return {
                    "id": r.element_id,
                    "type": r.type,
                    "properties": dict(r),
                    "source": r.start_node.get('id') if 'id' in r.start_node else r.start_node.element_id,
                    "target": r.end_node.get('id') if 'id' in r.end_node else r.end_node.element_id
                }
        return None
    
    def create_semantic_edge(self, source_id: str, target_id: str, weight: float):
        """Create a semantic RELATED_TO relationship"""
        query = """
        MATCH (a:Document {id: $source_id})
        MATCH (b:Document {id: $target_id})
        MERGE (a)-[r:RELATED_TO]->(b)
        SET r.weight = $weight, r.type = 'semantic'
        """
        with self.driver.get_session() as session:
            session.run(query, source_id=source_id, target_id=target_id, weight=weight)
    
    def create_entity_node(self, name: str, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """Create or merge an entity node"""
        query = """
        MERGE (e:Entity {name: $name, type: $type})
        ON CREATE SET e.id = $id
        RETURN e
        """
        with self.driver.get_session() as session:
            result = session.run(query, name=name, type=entity_type, id=entity_id)
            record = result.single()
            return dict(record['e']) if record else None
    
    def create_mentions_edge(self, doc_id: str, entity_name: str, entity_type: str):
        """Create MENTIONS relationship between document and entity"""
        query = """
        MATCH (d:Document {id: $doc_id})
        MATCH (e:Entity {name: $name, type: $type})
        MERGE (d)-[r:MENTIONS]->(e)
        SET r.weight = 1.0
        """
        with self.driver.get_session() as session:
            session.run(query, doc_id=doc_id, name=entity_name, type=entity_type)
    
    def delete_relationships(self, node_id: str, rel_types: List[str]):
        """Delete specific relationship types for a node"""
        rel_pattern = "|".join(rel_types)
        query = f"""
        MATCH (n {{id: $id}})-[r:{rel_pattern}]->()
        DELETE r
        """
        with self.driver.get_session() as session:
            session.run(query, id=node_id)
    
    def graph_search(self, start_id: str, depth: int, relationship_types: Optional[List[str]] = None) -> Dict:
        """Fetch nodes and relationships within depth"""
        rel_pattern = ""
        if relationship_types:
            safe_types = [t for t in relationship_types if t.isalnum() or "_" in t]
            if safe_types:
                rel_pattern = ":" + "|".join(safe_types)
        
        query = f"""
        MATCH (start {{id:$start_id}})-[{rel_pattern}*0..{depth}]-(n)
        WITH collect(distinct n) as nodes
        UNWIND nodes as source
        MATCH (source)-[r{rel_pattern}]->(target)
        WHERE target IN nodes
        RETURN source, r, target
        """
        
        data = {"nodes": [], "edges": [], "scored_edges": []}
        with self.driver.get_session() as session:
            res = session.run(query, start_id=start_id)
            seen_nodes = set()
            seen_edges = set()
            
            for record in res:
                source = record['source']
                target = record['target']
                rel = record['r']
                
                def get_node_id(node):
                    return node.get('id') or (node.element_id if hasattr(node, 'element_id') else str(node.id))
                
                source_id = get_node_id(source)
                target_id = get_node_id(target)
                
                if source_id not in seen_nodes:
                    s_dict = dict(source)
                    s_dict['id'] = source_id
                    data["nodes"].append(s_dict)
                    seen_nodes.add(source_id)
                
                if target_id not in seen_nodes:
                    t_dict = dict(target)
                    t_dict['id'] = target_id
                    data["nodes"].append(t_dict)
                    seen_nodes.add(target_id)
                
                edge_key = (source_id, target_id, rel.type)
                if edge_key not in seen_edges:
                    edge_weight = rel.get('weight', 1.0)
                    
                    # Basic edge data
                    edge_data = {
                        "source": source_id,
                        "target": target_id,
                        "type": rel.type,
                        "weight": edge_weight
                    }
                    data["edges"].append(edge_data)
                    
                    # Scored edge with additional context
                    source_text = source.get('text', '')[:100] if source.get('text') else source.get('name', '')
                    target_text = target.get('text', '')[:100] if target.get('text') else target.get('name', '')
                    
                    scored_edge = {
                        "source": source_id,
                        "target": target_id,
                        "type": rel.type,
                        "weight": edge_weight,
                        "score": edge_weight,  # Use weight as base score
                        "source_snippet": source_text,
                        "target_snippet": target_text,
                        "source_title": source.get('title', '') or source.get('name', ''),
                        "target_title": target.get('title', '') or target.get('name', '')
                    }
                    data["scored_edges"].append(scored_edge)
                    seen_edges.add(edge_key)
        
        # Sort scored edges by weight/score (descending)
        data["scored_edges"].sort(key=lambda x: x["score"], reverse=True)
        
        return data
    
    def get_connectivity_scores(self, candidate_ids: List[str]) -> Dict[str, float]:
        """Calculate connectivity scores for candidate documents"""
        query = """
        UNWIND $candidate_ids AS cid
        MATCH (c {id: cid})
        OPTIONAL MATCH (c)-[r]-(nbr)
        RETURN cid, sum(coalesce(r.weight, 1.0)) AS adj_weight
        """
        connectivity_scores = {}
        with self.driver.get_session() as session:
            res = session.run(query, candidate_ids=candidate_ids)
            for record in res:
                connectivity_scores[record["cid"]] = record["adj_weight"] or 0.0
        return connectivity_scores
    
    def find_entity_documents(self, entity_names: List[str], limit: int = 50) -> List[tuple]:
        """Find documents mentioning specific entities"""
        query = """
        UNWIND $names AS name
        MATCH (e:Entity) WHERE toLower(e.name) = toLower(name)
        MATCH (e)-[r]-(d:Document)
        RETURN d, r.weight AS edge_weight
        LIMIT $limit
        """
        results = []
        with self.driver.get_session() as session:
            res = session.run(query, names=entity_names, limit=limit)
            for record in res:
                # Convert Neo4j node to dictionary
                node_dict = dict(record["d"])
                edge_weight = record.get("edge_weight", 1.0)
                results.append((node_dict, edge_weight))
        return results
