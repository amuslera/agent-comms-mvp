import { Node, Edge, Position } from 'reactflow';

// Helper function to get the layouted elements (nodes and edges) with proper positioning
export const getLayoutedElements = (
  nodes: Node[],
  edges: Edge[],
  direction: 'TB' | 'LR' = 'TB', // Top to bottom or Left to right
  nodeWidth = 250,
  nodeHeight = 100,
  nodeSpacing = 50,
  levelSpacing = 100
) => {
  // Create a map of node IDs to their data
  const nodeMap = new Map(nodes.map(node => [node.id, node]));
  
  // Create a map of node IDs to their children
  const childrenMap = new Map<string, string[]>();
  const parentMap = new Map<string, string>();
  
  // Initialize children map with empty arrays
  nodes.forEach(node => {
    childrenMap.set(node.id, []);
  });
  
  // Build the parent-child relationships
  edges.forEach(edge => {
    const source = edge.source;
    const target = edge.target;
    
    // Add target as a child of source
    const children = childrenMap.get(source) || [];
    if (!children.includes(target)) {
      children.push(target);
      childrenMap.set(source, children);
    }
    
    // Set the parent of target
    if (!parentMap.has(target)) {
      parentMap.set(target, source);
    }
  });
  
  // Find root nodes (nodes with no parents)
  const rootNodes = nodes.filter(node => !parentMap.has(node.id));
  
  // Assign levels to each node
  const levels: Record<string, number> = {};
  
  // BFS to assign levels
  const queue: { id: string; level: number }[] = rootNodes.map(node => ({
    id: node.id,
    level: 0,
  }));
  
  while (queue.length > 0) {
    const { id, level } = queue.shift()!;
    
    // Skip if we've already processed this node with a lower level
    if (levels[id] !== undefined && levels[id] >= level) {
      continue;
    }
    
    levels[id] = level;
    
    // Add children to the queue
    const children = childrenMap.get(id) || [];
    children.forEach(childId => {
      queue.push({ id: childId, level: level + 1 });
    });
  }
  
  // Group nodes by level
  const nodesByLevel: Record<number, string[]> = {};
  Object.entries(levels).forEach(([nodeId, level]) => {
    if (!nodesByLevel[level]) {
      nodesByLevel[level] = [];
    }
    nodesByLevel[level].push(nodeId);
  });
  
  // Calculate positions for each node
  const positionedNodes = nodes.map(node => {
    const level = levels[node.id] || 0;
    const nodesInLevel = nodesByLevel[level] || [];
    const index = nodesInLevel.indexOf(node.id);
    
    // Calculate position based on direction
    let x, y;
    if (direction === 'TB') {
      // Top to bottom layout
      x = (index - (nodesInLevel.length - 1) / 2) * (nodeWidth + nodeSpacing);
      y = level * (nodeHeight + levelSpacing);
    } else {
      // Left to right layout
      x = level * (nodeWidth + levelSpacing);
      y = (index - (nodesInLevel.length - 1) / 2) * (nodeHeight + nodeSpacing);
    }
    
    return {
      ...node,
      position: { x, y },
      sourcePosition: direction === 'TB' ? Position.Bottom : Position.Right,
      targetPosition: direction === 'TB' ? Position.Top : Position.Left,
    };
  });
  
  return {
    nodes: positionedNodes,
    edges,
  };
};

// Helper function to get the dimensions of the graph
export const getGraphDimensions = (nodes: Node[]) => {
  if (nodes.length === 0) {
    return { width: 0, height: 0 };
  }
  
  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  
  nodes.forEach(node => {
    const { x, y } = node.position;
    const width = node.width || 250;
    const height = node.height || 100;
    
    minX = Math.min(minX, x - width / 2);
    maxX = Math.max(maxX, x + width / 2);
    minY = Math.min(minY, y - height / 2);
    maxY = Math.max(maxY, y + height / 2);
  });
  
  return {
    width: maxX - minX,
    height: maxY - minY,
  };
};
