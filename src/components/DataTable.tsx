import { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ChevronLeft, ChevronRight, Search, ChevronUp, ChevronDown } from 'lucide-react';

interface Column {
  accessorKey?: string;
  id?: string;
  header: string;
  cell?: ({ getValue, row }: any) => React.ReactNode;
}

interface DataTableProps {
  data: any[];
  columns: Column[];
  loading?: boolean;
  searchable?: boolean;
  onSearchChange?: (searchTerm: string) => void;
  externalSearchTerm?: string;
  externalSortConfig?: {
    key: string | null;
    direction: 'asc' | 'desc';
  };
  onSortChange?: (sortConfig: { key: string | null; direction: 'asc' | 'desc' }) => void;
}

export const DataTable = ({ data, columns, loading, searchable = true, onSearchChange, externalSearchTerm, externalSortConfig, onSortChange }: DataTableProps) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [localSearchTerm, setLocalSearchTerm] = useState('');
  const [localSortConfig, setLocalSortConfig] = useState<{
    key: string | null;
    direction: 'asc' | 'desc';
  }>({ key: null, direction: 'asc' });
  const itemsPerPage = 10;

  // Use external search term if provided, otherwise use local
  const searchTerm = externalSearchTerm !== undefined ? externalSearchTerm : localSearchTerm;
  
  // Use external sort config if provided, otherwise use local
  const sortConfig = externalSortConfig !== undefined ? externalSortConfig : localSortConfig;

  // Sorting function
  const sortData = (data: any[]) => {
    if (!sortConfig.key) return data;

    return [...data].sort((a, b) => {
      let aValue = a[sortConfig.key!];
      let bValue = b[sortConfig.key!];

      // Handle null/undefined values
      if (aValue == null) aValue = '';
      if (bValue == null) bValue = '';

      // Determine if values are numeric and sort accordingly
      const aNum = Number(aValue);
      const bNum = Number(bValue);
      
      // Check if both values are valid numbers
      if (!isNaN(aNum) && !isNaN(bNum)) {
        // Numeric sorting
        if (aNum < bNum) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (aNum > bNum) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      } else {
        // String sorting for non-numeric values
        aValue = String(aValue).toLowerCase();
        bValue = String(bValue).toLowerCase();

        if (aValue < bValue) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (aValue > bValue) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      }
    });
  };

  // Handle column sorting
  const handleSort = (key: string) => {
    const newSortConfig = {
      key,
      direction: sortConfig.key === key && sortConfig.direction === 'asc' ? 'desc' : 'asc'
    };
    
    if (onSortChange) {
      onSortChange(newSortConfig);
    } else {
      setLocalSortConfig(newSortConfig);
    }
    
    setCurrentPage(1); // Reset to first page when sorting
  };

  const filteredData = searchTerm
    ? data.filter(item =>
        Object.values(item).some(value =>
          String(value).toLowerCase().includes(searchTerm.toLowerCase())
        )
      )
    : data;

  // Apply sorting to filtered data
  const sortedData = sortData(filteredData);

  const totalPages = Math.ceil(sortedData.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedData = sortedData.slice(startIndex, startIndex + itemsPerPage);

  if (loading) {
    return (
      <div className="p-8 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-guild-accent-1 mx-auto"></div>
        <p className="mt-2 text-muted-foreground">Loading data...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 p-4">
      {searchable && (
        <div className="flex items-center gap-2">
          <Search className="w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search all fields..."
            value={searchTerm}
            onChange={(e) => {
              const value = e.target.value;
              if (onSearchChange) {
                onSearchChange(value);
              } else {
                setLocalSearchTerm(value);
              }
            }}
            className="max-w-sm"
          />
        </div>
      )}

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((column) => {
                const key = column.accessorKey || column.id;
                const isSorted = sortConfig.key === key;
                
                return (
                  <TableHead 
                    key={key}
                    className="cursor-pointer hover:bg-muted/50 transition-colors"
                    onClick={() => key && handleSort(key)}
                  >
                    <div className="flex items-center gap-2">
                      <span>{column.header}</span>
                      {isSorted && (
                        <span className="text-guild-accent-1">
                          {sortConfig.direction === 'asc' ? (
                            <ChevronUp className="w-4 h-4" />
                          ) : (
                            <ChevronDown className="w-4 h-4" />
                          )}
                        </span>
                      )}
                    </div>
                  </TableHead>
                );
              })}
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginatedData.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length} className="text-center py-8">
                  No data available
                </TableCell>
              </TableRow>
            ) : (
              paginatedData.map((row, index) => (
                <TableRow key={index}>
                  {columns.map((column) => (
                    <TableCell key={column.accessorKey || column.id}>
                      {column.cell
                        ? column.cell({ 
                            getValue: () => row[column.accessorKey || ''],
                            row: { original: row }
                          })
                        : row[column.accessorKey || '']
                      }
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {startIndex + 1} to {Math.min(startIndex + itemsPerPage, sortedData.length)} of{' '}
            {sortedData.length} results
          </p>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
            >
              <ChevronLeft className="w-4 h-4" />
              Previous
            </Button>
            
            <span className="text-sm">
              Page {currentPage} of {totalPages}
            </span>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};