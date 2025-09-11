#!/usr/bin/env python3
"""
Quick test script to check Neo4j connection with different authentication methods.
"""
import asyncio
import logging
import os
from neo4j import AsyncGraphDatabase
from src.qc.core.neo4j_manager import EnhancedNeo4jManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_no_auth_connection():
    """Test connection without authentication"""
    try:
        logger.info("Testing connection without authentication...")
        driver = AsyncGraphDatabase.driver("bolt://localhost:7687")
        
        async with driver.session() as session:
            result = await session.run("RETURN 'Connected!' as message")
            record = await result.single()
            logger.info(f"SUCCESS: {record['message']}")
            
            # Test basic query
            result = await session.run("MATCH (n) RETURN count(n) as node_count")
            record = await result.single()
            logger.info(f"Total nodes in database: {record['node_count']}")
            
        await driver.close()
        return True
        
    except Exception as e:
        logger.error(f"No-auth connection failed: {e}")
        return False

async def test_enhanced_manager_no_auth():
    """Test EnhancedNeo4jManager with no authentication"""
    try:
        logger.info("Testing EnhancedNeo4jManager with no authentication...")
        
        # Force no authentication by setting empty values
        os.environ.pop('NEO4J_USERNAME', None)
        os.environ.pop('NEO4J_PASSWORD', None)
        
        manager = EnhancedNeo4jManager()
        await manager.connect()
        
        # Test a simple query
        result = await manager.execute_query("MATCH (n) RETURN count(n) as total")
        if result:
            logger.info(f"SUCCESS: Found {result[0]['total']} nodes in database")
        
        await manager.close()
        return True
        
    except Exception as e:
        logger.error(f"EnhancedNeo4jManager connection failed: {e}")
        return False

async def test_default_credentials():
    """Test with default Neo4j credentials"""
    try:
        logger.info("Testing with default credentials (neo4j/neo4j)...")
        driver = AsyncGraphDatabase.driver(
            "bolt://localhost:7687", 
            auth=("neo4j", "neo4j")
        )
        
        async with driver.session() as session:
            result = await session.run("RETURN 'Connected with auth!' as message")
            record = await result.single()
            logger.info(f"SUCCESS: {record['message']}")
            
        await driver.close()
        return True
        
    except Exception as e:
        logger.error(f"Default credentials failed: {e}")
        return False

async def main():
    """Test different connection methods"""
    logger.info("🔍 TESTING NEO4J CONNECTION METHODS")
    logger.info("="*50)
    
    # Test 1: No authentication
    success1 = await test_no_auth_connection()
    
    # Test 2: Enhanced manager with no auth
    success2 = await test_enhanced_manager_no_auth()
    
    # Test 3: Default credentials
    success3 = await test_default_credentials()
    
    logger.info("\n" + "="*50)
    logger.info("CONNECTION TEST RESULTS:")
    logger.info(f"No auth connection: {'SUCCESS' if success1 else 'FAILED'}")
    logger.info(f"Enhanced manager: {'SUCCESS' if success2 else 'FAILED'}")
    logger.info(f"Default credentials: {'SUCCESS' if success3 else 'FAILED'}")
    
    if any([success1, success2, success3]):
        logger.info("✅ Found working connection method")
        return True
    else:
        logger.info("❌ All connection methods failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)