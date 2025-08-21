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
import { ChevronLeft, ChevronRight, Search, ChevronUp, ChevronDown, X } from 'lucide-react';

interface Column {
  accessorKey?: string;
  id?: string;
  header: string;
  cell?: ({ getValue, row }: any) => React.ReactNode;
}

interface SortConfig {
  key: string;
  direction: 'asc' | 'desc';
  priority: number; // Lower number = higher priority
}

interface DataTableProps {
  data: any[];
  columns: Column[];
  loading?: boolean;
  searchable?: boolean;
  onSearchChange?: (searchTerm: string) => void;
  externalSearchTerm?: string;
  externalSortConfig?: SortConfig[];
  onSortChange?: (sortConfig: SortConfig[]) => void;
  isMobile?: boolean;
}

export const DataTable = ({ data, columns, loading, searchable = true, onSearchChange, externalSearchTerm, externalSortConfig, onSortChange, isMobile = false }: DataTableProps) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [localSearchTerm, setLocalSearchTerm] = useState('');
  const [localSortConfig, setLocalSortConfig] = useState<SortConfig[]>([]);
  const itemsPerPage = 10;

  // Use external search term if provided, otherwise use local
  const searchTerm = externalSearchTerm !== undefined ? externalSearchTerm : localSearchTerm;
  
  // Use external sort config if provided, otherwise use local
  // Ensure sortConfig is always an array to prevent "not iterable" errors
  const sortConfig = (externalSortConfig !== undefined ? externalSortConfig : localSortConfig) || [];

  // Sorting function for multiple columns
  const sortData = (data: any[]) => {
    // Ensure sortConfig is an array and has items
    if (!Array.isArray(sortConfig) || sortConfig.length === 0) return data;

    // Sort by priority (lower number = higher priority)
    const sortedConfig = [...sortConfig].sort((a, b) => a.priority - b.priority);

    return [...data].sort((a, b) => {
      for (const config of sortedConfig) {
        let aValue = a[config.key];
        let bValue = b[config.key];

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
            return config.direction === 'asc' ? -1 : 1;
          }
          if (aNum > bNum) {
            return config.direction === 'asc' ? 1 : -1;
          }
          // If equal, continue to next sort column
          continue;
        } else {
          // String sorting for non-numeric values
          aValue = String(aValue).toLowerCase();
          bValue = String(bValue).toLowerCase();

          if (aValue < bValue) {
            return config.direction === 'asc' ? -1 : 1;
          }
          if (aValue > bValue) {
            return config.direction === 'asc' ? 1 : -1;
          }
          // If equal, continue to next sort column
          continue;
        }
      }
      return 0; // All sort columns are equal
    });
  };

  // Handle column sorting
  const handleSort = (key: string) => {
    let newSortConfig: SortConfig[];
    
    // Ensure sortConfig is an array
    const currentSortConfig = Array.isArray(sortConfig) ? sortConfig : [];
    
    // Check if column is already in sort config
    const existingIndex = currentSortConfig.findIndex(config => config.key === key);
    
    if (existingIndex >= 0) {
      const existing = sortConfig[existingIndex];
      
      // Cycle through: asc -> desc -> remove
      if (existing.direction === 'asc') {
        // Change to desc
        newSortConfig = currentSortConfig.map((config, index) => 
          index === existingIndex 
            ? { ...config, direction: 'desc' as const }
            : config
        );
      } else {
        // Remove this column from sorting
        newSortConfig = currentSortConfig.filter((_, index) => index !== existingIndex);
      }
    } else {
      // Add new column with highest priority (lowest number)
      const newPriority = currentSortConfig.length > 0 ? Math.max(...currentSortConfig.map(c => c.priority)) + 1 : 1;
      newSortConfig = [...currentSortConfig, { key, direction: 'asc', priority: newPriority }];
    }
    
    if (onSortChange) {
      onSortChange(newSortConfig);
    } else {
      setLocalSortConfig(newSortConfig);
    }
    
    setCurrentPage(1); // Reset to first page when sorting
  };

  // Remove a column from sorting
  const removeSort = (key: string) => {
    // Ensure sortConfig is an array
    const currentSortConfig = Array.isArray(sortConfig) ? sortConfig : [];
    const newSortConfig = currentSortConfig.filter(config => config.key !== key);
    
    if (onSortChange) {
      onSortChange(newSortConfig);
    } else {
      setLocalSortConfig(newSortConfig);
    }
    
    setCurrentPage(1);
  };

  // Get sort info for a column
  const getColumnSortInfo = (key: string) => {
    // Ensure sortConfig is an array
    const currentSortConfig = Array.isArray(sortConfig) ? sortConfig : [];
    const config = currentSortConfig.find(c => c.key === key);
    if (!config) return null;
    
    return {
      direction: config.direction,
      priority: config.priority
    };
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
            className={isMobile ? "flex-1" : "max-w-sm"}
          />
        </div>
      )}



      {/* Mobile Card Layout */}
      {isMobile ? (
        <div className="space-y-3 p-4">
          {paginatedData.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground">No data available</p>
            </div>
          ) : (
            paginatedData.map((row, index) => (
              <div key={index} className="border rounded-lg p-4 space-y-3 bg-card">
                {columns.map((column) => {
                  const key = column.accessorKey || column.id;
                  if (key === 'actions') return null; // Skip actions column in mobile view
                  
                  return (
                    <div key={key} className="flex flex-col space-y-1">
                      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                        {column.header}
                      </span>
                      <div className="text-sm">
                        {column.cell
                          ? column.cell({ 
                              getValue: () => row[column.accessorKey || ''],
                              row: { original: row }
                            })
                          : row[column.accessorKey || '']
                        }
                      </div>
                    </div>
                  );
                })}
                {/* Mobile Actions */}
                <div className="flex flex-col space-y-2 pt-2 border-t">
                  <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Actions
                  </span>
                  <div className="flex gap-2">
                    {columns.find(col => col.id === 'actions')?.cell?.({ 
                      getValue: () => row[columns.find(col => col.id === 'actions')?.accessorKey || ''],
                      row: { original: row }
                    })}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      ) : (
        /* Desktop Table Layout */
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                {columns.map((column) => {
                  const key = column.accessorKey || column.id;
                  const sortInfo = getColumnSortInfo(key);
                  
                  return (
                    <TableHead 
                      key={key}
                      className="cursor-pointer hover:bg-muted/50 transition-colors"
                      onClick={() => key && handleSort(key)}
                    >
                      <div className="flex items-center gap-2">
                        <span>{column.header}</span>
                        {sortInfo && (
                          <div className="flex items-center gap-1">
                            <span className="text-guild-accent-1">
                              {sortInfo.direction === 'asc' ? (
                                <ChevronUp className="w-4 h-4" />
                              ) : (
                                <ChevronDown className="w-4 h-4" />
                              )}
                            </span>
                            <span className="text-xs text-muted-foreground bg-muted px-1 rounded">
                              {sortInfo.priority}
                            </span>
                          </div>
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
      )}

      {totalPages > 1 && (
        <div className={`flex ${isMobile ? 'flex-col space-y-4' : 'items-center justify-between'}`}>
          <p className="text-sm text-muted-foreground text-center md:text-left">
            Showing {startIndex + 1} to {Math.min(startIndex + itemsPerPage, sortedData.length)} of{' '}
            {sortedData.length} results
          </p>
          
          <div className="flex items-center justify-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
            >
              <ChevronLeft className="w-4 h-4" />
              {!isMobile && 'Previous'}
            </Button>
            
            <span className="text-sm px-2">
              {currentPage} / {totalPages}
            </span>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
            >
              {!isMobile && 'Next'}
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};