from flask import Flask, request, jsonify
import sys

app = Flask(__name__)

# Global data structures to hold bus stands and edges
bus_stand_to_index = {}
edges = []

def floyd_warshall(n, edges):
    # Initialize the distance and next matrices
    dist = [[sys.maxsize] * n for _ in range(n)]
    next_node = [[-1] * n for _ in range(n)]
    
    # Distance from a node to itself is 0
    for i in range(n):
        dist[i][i] = 0
    
    # Fill the matrix with the initial distances and set up the path
    for frm, to, weight in edges:
        dist[frm][to] = weight
        next_node[frm][to] = to
    
    # Floyd-Warshall algorithm with path reconstruction
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] < sys.maxsize and dist[k][j] < sys.maxsize:
                    if dist[i][j] > dist[i][k] + dist[k][j]:
                        dist[i][j] = dist[i][k] + dist[k][j]
                        next_node[i][j] = next_node[i][k]
    
    return dist, next_node

def reconstruct_path(start, end, next_node):
    # Reconstruct the shortest path from start to end
    if next_node[start][end] == -1:
        return None  # No path exists
    path = [start]
    while start != end:
        start = next_node[start][end]
        path.append(start)
    return path

@app.route('/add_edge', methods=['POST'])
def add_edge():
    global bus_stand_to_index, edges
    data = request.json
    frm = data.get('from')
    to = data.get('to')
    distance = data.get('distance')
    
    if frm is None or to is None or distance is None:
        return jsonify({'error': 'Invalid input. Please provide "from", "to", and "distance".'}), 400
    
    # Assign indices to bus stands if not already assigned
    if frm not in bus_stand_to_index:
        bus_stand_to_index[frm] = len(bus_stand_to_index)
    if to not in bus_stand_to_index:
        bus_stand_to_index[to] = len(bus_stand_to_index)
    
    # Convert bus stand names to indices for edges
    frm_index = bus_stand_to_index[frm]
    to_index = bus_stand_to_index[to]
    edges.append((frm_index, to_index, distance))
    
    return jsonify({'message': f'Edge added from {frm} to {to} with distance {distance}.'})

@app.route('/shortest_path', methods=['POST'])
def shortest_path():
    global bus_stand_to_index, edges
    data = request.json
    start_name = data.get('start')
    end_name = data.get('end')
    
    if start_name not in bus_stand_to_index or end_name not in bus_stand_to_index:
        return jsonify({'error': 'Invalid bus stand name(s).'}), 400
    
    # Get the number of bus stands
    n = len(bus_stand_to_index)
    
    # Run Floyd-Warshall algorithm
    dist, next_node = floyd_warshall(n, edges)
    
    # Get indices of start and end bus stands
    start = bus_stand_to_index[start_name]
    end = bus_stand_to_index[end_name]
    
    # Find the shortest path and distance
    path = reconstruct_path(start, end, next_node)
    if path is None:
        return jsonify({'message': f'No path exists from {start_name} to {end_name}.'}), 404
    
    # Convert path from indices to bus stand names
    index_to_bus_stand = {index: name for name, index in bus_stand_to_index.items()}
    path_names = [index_to_bus_stand[idx] for idx in path]
    return jsonify({
        'shortest_path': path_names,
        'total_distance': dist[start][end]
    })

@app.route('/reset', methods=['POST'])
def reset():
    global bus_stand_to_index, edges
    bus_stand_to_index.clear()
    edges.clear()
    return jsonify({'message': 'Data reset successful.'})

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
