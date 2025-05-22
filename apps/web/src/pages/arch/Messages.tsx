import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { RefreshCw, Search } from 'lucide-react';

interface Message {
  id: string;
  timestamp: string;
  type: string;
  sender: string;
  content: any;
  metadata?: {
    priority?: number;
    status?: string;
  };
}

const MessagesPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchMessages = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // In a real app, this would be an API call to your backend
      // const response = await fetch('/api/arch/messages');
      // const data = await response.json();
      
      // Mock data for development
      const mockMessages: Message[] = [
        {
          id: 'msg-001',
          timestamp: new Date(Date.now() - 60000).toISOString(),
          type: 'task_result',
          sender: 'AGENT-CC',
          content: 'Successfully processed task TASK-042',
          metadata: { status: 'success' }
        },
        {
          id: 'msg-002',
          timestamp: new Date(Date.now() - 120000).toISOString(),
          type: 'error',
          sender: 'AGENT-CA',
          content: 'Failed to process task: Invalid input format',
          metadata: { priority: 1 }
        },
        {
          id: 'msg-003',
          timestamp: new Date(Date.now() - 1800000).toISOString(),
          type: 'status_update',
          sender: 'AGENT-WA',
          content: 'Completed UI updates for dashboard',
          metadata: { status: 'info' }
        },
      ];
      
      setMessages(mockMessages);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error fetching messages:', err);
      setError('Failed to load messages. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMessages();
    
    // Set up polling (every 30 seconds)
    const intervalId = setInterval(fetchMessages, 30000);
    
    // Clean up interval on component unmount
    return () => clearInterval(intervalId);
  }, []);

  const filteredMessages = messages.filter(message => 
    message.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
    message.sender.toLowerCase().includes(searchTerm.toLowerCase()) ||
    message.type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getMessageTypeColor = (type: string) => {
    switch (type) {
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'task_result':
        return 'bg-green-100 text-green-800';
      case 'status_update':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">ARCH Message Center</h1>
        <div className="flex items-center space-x-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={fetchMessages}
            disabled={isLoading}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {lastUpdated && (
            <span className="text-sm text-gray-500">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      <Card className="mb-6">
        <div className="p-4 border-b">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              type="text"
              placeholder="Search messages..."
              className="pl-10"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
        
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-gray-500">
              <RefreshCw className="mx-auto h-8 w-8 animate-spin" />
              <p className="mt-2">Loading messages...</p>
            </div>
          ) : error ? (
            <div className="p-8 text-center text-red-500">
              <p>{error}</p>
              <Button 
                variant="outline" 
                className="mt-4" 
                onClick={fetchMessages}
              >
                Retry
              </Button>
            </div>
          ) : filteredMessages.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              {searchTerm ? 'No matching messages found' : 'No messages available'}
            </div>
          ) : (
            <div className="divide-y">
              {filteredMessages.map((message) => (
                <div key={message.id} className="p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getMessageTypeColor(message.type)}`}>
                          {message.type.replace('_', ' ')}
                        </span>
                        <span className="font-medium text-gray-900">{message.sender}</span>
                        <span className="text-sm text-gray-500">
                          {formatTimestamp(message.timestamp)}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-gray-700">{message.content}</p>
                    </div>
                    {message.metadata?.priority && (
                      <span className="text-xs text-gray-500">
                        Priority: {message.metadata.priority}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default MessagesPage;
